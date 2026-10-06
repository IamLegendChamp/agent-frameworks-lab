import logging
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from task_data import chunks

from logging_setup import setup_logging

logger = logging.getLogger(__name__)



def main():
    setup_logging()
    # logger.info("loaded %d chunks", len(chunks))

    first = chunks[0]
    # doc = Document(text=first["text"], metadata={"chunk_id": first["chunk_id"]})
    # logger.info("doc id=%s chunk_id=%s", doc.doc_id, doc.metadata["chunk_id"])

    docs = []
    for chunk in chunks:
        docs.append(Document(text=chunk["text"], metadata={"chunk_id": chunk["chunk_id"]}))
    logger.info("built %d documents, last chunk_id=%s", len(docs), docs[-1].metadata["chunk_id"])

    splitter = SentenceSplitter(chunk_size=30, chunk_overlap=5)


if __name__ == "__main__":
    main()
