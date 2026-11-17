import logging
import os

PROJECT_LOGGERS = ("__main__", "gateway", "limiter", "task_data", "llama_docs")
QUIET_LOGGERS = ("llama_index", "httpx", "httpcore", "fsspec", "asyncio")


def setup_logging() -> None:
    """Configure logging once per entry point.

    Third-party loggers stay at WARNING; this project's loggers use LOG_LEVEL.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=logging.WARNING, format="line %(lineno)d -> %(message)s")
    for name in PROJECT_LOGGERS:
        logging.getLogger(name).setLevel(level)
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
