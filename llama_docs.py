import logging
import os
from dotenv import load_dotenv

from llama_index.core import Document
from llama_index.core.node_parser import (
    SentenceSplitter, TokenTextSplitter, 
    SentenceWindowNodeParser, HierarchicalNodeParser, 
    get_leaf_nodes, SemanticSplitterNodeParser
)
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from task_data import chunks

from logging_setup import setup_logging

logger = logging.getLogger(__name__)
load_dotenv()

def show_chunk(label, node_list, chunk_id):
    for node in node_list:
        if node.metadata["chunk_id"] == chunk_id:
            logger.info("%s %s %s", label, chunk_id, node.text)

def main():
    setup_logging()
    # logger.info("loaded %d chunks", len(chunks))

    first = chunks[0]
    # doc = Document(text=first["text"], metadata={"chunk_id": first["chunk_id"]})
    # logger.info("doc id=%s chunk_id=%s", doc.doc_id, doc.metadata["chunk_id"])

    docs = []
    for chunk in chunks:
        # logger.info("%s\n", chunk["text"])
        docs.append(Document(text=chunk["text"], metadata={"chunk_id": chunk["chunk_id"]}))
    # logger.info("built %d documents, last chunk_id=%s", len(docs), docs[-1].metadata["chunk_id"])

    splitter = SentenceSplitter(chunk_size=30, chunk_overlap=5)
    nodes = splitter.get_nodes_from_documents(docs)
    # logger.info("%d documents -> %d nodes", len(docs), len(nodes))
    # for i, node in enumerate(nodes):
    #     logger.debug("node=%d chunk_id=%s chars=%d", i, node.metadata["chunk_id"], len(node.text))
    # logger.info("node 3: %s", nodes[3].text)
    # logger.info("node 4: %s", nodes[4].text)

    token_splitter = TokenTextSplitter(chunk_size=30, chunk_overlap=5)
    token_nodes = token_splitter.get_nodes_from_documents(docs)
    # logger.info("token splitter: %d nodes", len(token_nodes))
    # for node in token_nodes:
    #     if node.metadata["chunk_id"] == "C004":
    #         logger.info("token C004: %s", node.text)

    window_parser = SentenceWindowNodeParser.from_defaults(window_size=1, window_metadata_key="window", original_text_metadata_key="original_sentence")
    window_nodes = window_parser.get_nodes_from_documents(docs)
    # logger.info("window parser: %d nodes", len(window_nodes))
    # for node in window_nodes:
    #     if node.metadata["chunk_id"] == "C004":
    #         logger.info("window C004: sentence=%s", node.metadata["original_sentence"])
    #         logger.info("window C004: window=%s", node.metadata["window"])

    show_chunk("sentence", nodes, "C007")
    show_chunk("token", token_nodes, "C007")
    show_chunk("window", window_nodes, "C007")

    hier_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[120, 60, 30], chunk_overlap=5)
    hier_nodes = hier_parser.get_nodes_from_documents(docs)
    logger.info("hierarchical: %d nodes in total, %d leaf nodes", len(hier_nodes), len(get_leaf_nodes(hier_nodes)))

    embed_model = GoogleGenAIEmbedding(model_name=os.getenv("GEMINI_EMBED_MODEL"))
    semantic_parser = SemanticSplitterNodeParser(embed_model=embed_model, buffer_size=1, breakpoint_percentile_threshold=95)
    long_text = " ".join(chunk["text"] for chunk in chunks)
    logger.info("long text: %d characters", len(long_text))
    long_doc = Document(text=long_text)
    semantic_nodes = semantic_parser.get_nodes_from_documents([long_doc])
    logger.info("semantic splitter: %d nodes", len(semantic_nodes))
    for node in semantic_nodes:
        logger.info("semantic node: %s", node.text[:70])
        
            

if __name__ == "__main__":
    main()
