import logging
import os

def setup_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.debug("debug: tiny detail for developers")
    logger.info("info: normal progress")
    logger.warning("warning: something odd, still running")
    logger.error("error: something failed")


if __name__ == "__main__":
    main()