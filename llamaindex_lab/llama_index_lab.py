import logging
import os
import re

from dotenv import load_dotenv
from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI

from logging_setup import setup_logging
from task_data import chunks, questions

logger = logging.getLogger(__name__)
load_dotenv()


def cited_numbers(answer_text: str) -> list[int]:
    brackets = re.findall(r"\[([^\]]+)\]", answer_text)
    numbers = []
    for block in brackets:
        numbers.extend(re.findall(r"\d+", block))
    return [int(n) for n in numbers]


def cited_chunk_ids(response) -> list[str]:
    ids = []
    for n in cited_numbers(response.response):
        if 1 <= n <= len(response.source_nodes):
            ids.append(response.source_nodes[n - 1].node.metadata["chunk_id"])
        else:
            logger.warning("citation [%d] has no matching source", n)
    return ids


def check_golden(q: dict, response) -> bool:
    cited = set(cited_chunk_ids(response))
    expected = set(q["expected_chunk_ids"])
    missing = [w for w in q["answer_must_contain"] if w.lower() not in response.response.lower()]
    passed = expected <= cited and not missing
    logger.info(
        "%s %s cited=%s expected=%s missing=%s",
        q["id"], "PASS" if passed else "FAIL", sorted(cited), sorted(expected), missing,
    )
    if not passed:
        logger.info("%s answer=%s", q["id"], response.response)
    return passed


def own_answer(index, llm, question: str) -> str:
    nodes = index.as_retriever(similarity_top_k=3).retrieve(question)
    context = "\n".join(f"[{n.node.metadata['chunk_id']}] {n.node.text}" for n in nodes)
    logger.debug("own context for %r: %s", question, context.replace("\n", " | "))
    prompt = (
        "Answer only using the sources below. "
        "After each fact, cite the source id in square brackets, like [C001]. "
        "Include every deadline, condition and exception that applies. "
        "If the sources do not contain the answer, say so.\n\n"
        f"Sources:\n{context}\n\n"
        f"Question: {question}\nAnswer:"
    )
    return llm.complete(prompt).text


def check_golden_own(q: dict, answer_text: str) -> bool:
    cited = set(re.findall(r"C\d{3}", answer_text))
    expected = set(q["expected_chunk_ids"])
    missing = [w for w in q["answer_must_contain"] if w.lower() not in answer_text.lower()]
    passed = expected <= cited and not missing
    logger.info(
        "own %s %s cited=%s expected=%s missing=%s",
        q["id"], "PASS" if passed else "FAIL", sorted(cited), sorted(expected), sorted(missing),
    )
    if not passed:
        logger.info("own %s answer=%s", q["id"], answer_text)
    return passed


def main():
    setup_logging()
    embed_model = GoogleGenAIEmbedding(model_name=os.getenv("GEMINI_EMBED_MODEL"))
    if os.path.isdir("storage"):
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = load_index_from_storage(storage_context, embed_model=embed_model)
        logger.info("loaded index with %d vectors", len(index.vector_store.data.embedding_dict))
    else:
        docs = [Document(text=c["text"], metadata={"chunk_id": c["chunk_id"]}) for c in chunks]
        nodes = SentenceSplitter(chunk_size=30, chunk_overlap=5).get_nodes_from_documents(docs)
        index = VectorStoreIndex(nodes, embed_model=embed_model)
        index.storage_context.persist(persist_dir="storage")
        logger.info("built index with %d vectors", len(index.vector_store.data.embedding_dict))

    llm = GoogleGenAI(model=os.getenv("GEMINI_CHAT_MODEL"))
    citation_engine = CitationQueryEngine.from_args(index, llm=llm, similarity_top_k=3)

    passed_count = 0
    for q in questions:
        if check_golden(q, citation_engine.query(q["question"])):
            passed_count += 1
    logger.info("library citations pass rate=%d/%d", passed_count, len(questions))

    own_passed = 0
    for q in questions:
        if check_golden_own(q, own_answer(index, llm, q["question"])):
            own_passed += 1
    logger.info("own prompt pass rate=%d/%d", own_passed, len(questions))


if __name__ == "__main__":
    main()
