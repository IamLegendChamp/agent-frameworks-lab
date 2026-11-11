import logging

from langchain_lab.policy_tools import search_policy
from logging_setup import setup_logging

logger = logging.getLogger(__name__)

def main() -> None:
    setup_logging()
    bad_inputs = [{"keyword": 123}, {}, {"keyword": "return", "extra": 1}]
    for args in bad_inputs:
        try:
            out = search_policy.invoke(args)
            logger.info("args %s -> ok: %r", args, out[:60])
        except Exception as exc:
            logger.warning("args %s -> %s", args, type(exc).__name__)
            logger.warning("reason: %s", str(exc).splitlines()[0])

if __name__ == "__main__":
    main()
