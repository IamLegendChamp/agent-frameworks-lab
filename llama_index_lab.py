import logging
from llama_index.core import VectorStoreIndex, Document, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from logging_setup import setup_logging
from task_data import chunks
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from dotenv import load_dotenv
from llama_index.llms.google_genai import GoogleGenAI
import os

logger = logging.getLogger(__name__)
load_dotenv()


def main():
    setup_logging()
    docs = [Document(text=c["text"], metadata={"chunk_id": c["chunk_id"]}) for c in chunks]
    logger.info("built %d documents", len(docs))
    splitter = SentenceSplitter(chunk_size=30, chunk_overlap=5)
    nodes = splitter.get_nodes_from_documents(docs)
    logger.info("%d documents -> %d nodes", len(docs), len(nodes))
    embed_model = GoogleGenAIEmbedding(model_name="gemini-embedding-001")
    index = VectorStoreIndex(nodes, embed_model=embed_model)
    logger.info("index built with %d vectors", len(index.vector_store.data.embedding_dict))
    retriever = index.as_retriever(similarity_top_k=3)
    results = retriever.retrieve("What is the return window for unused items?")
    for r in results:
        logger.info("score=%.4f chunk_id=%s text=%s", r.score, r.node.metadata["chunk_id"], r.node.text)
    llm = GoogleGenAI(model=os.getenv("GEMINI_CHAT_MODEL"))
    query_engine = index.as_query_engine(llm=llm, embed_model=embed_model, similarity_top_k=3)
    response = query_engine.query("What is the return window for unused items?")
    logger.info("answer=%s", response.response)
    for sn in response.source_nodes:
        logger.info("source score=%.4f chunk_id=%s", sn.score, sn.node.metadata["chunk_id"])
    index.storage_context.persist(persist_dir="storage")
    storage_context = StorageContext.from_defaults(persist_dir="storage")
    loaded_index = load_index_from_storage(storage_context, embed_model=embed_model)
    logger.info("reloaded index with %d vectors", len(loaded_index.vector_store.data.embedding_dict))
    for r in loaded_index.as_retriever(similarity_top_k=1).retrieve("What is the return window for unused items?"):
        logger.info("reloaded top hit score=%.4f chunk_id=%s", r.score, r.node.metadata["chunk_id"])
        
    
if __name__ == "__main__":
    main()
