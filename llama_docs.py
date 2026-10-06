import logging
from llama_index.core import Document
from task_data import chunks

from logging_setup import setup_logging

logger = logging.getLogger(__name__)



def main():
    setup_logging()
    logger.info("loaded %d chunks", len(chunks))

if __name__ == "__main__":
    main()
    