import logging
import os

def setup_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    # log_format = "%(asctime)s %(levelname)s %(name)s: %(message)s" if os.getenv("LOG_PREFIX") == "1" else "%(message)s"
    # log_format = "%(filename)s:%(lineno)d -> %(message)s " if os.getenv("LOG_PREFIX") == "1" else "%(message)s"
    log_format = "line %(lineno)d -> %(message)s"
    logging.basicConfig(
        level=level,
        format=log_format,
    )
    logging.getLogger("llama_index").setLevel(logging.WARNING)  
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    # logger.debug("debug: tiny detail for developers")
    # logger.info("info: normal progress")
    # logger.warning("warning: something odd, still running")
    # logger.error("error: something failed")

    chunk_count = 10
    logger.info("loaded %d chunks from %s", chunk_count, "policy_chunks.jsonl")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("could not divide")


if __name__ == "__main__":
    main()