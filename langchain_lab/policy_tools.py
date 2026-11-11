from langchain_core.tools import tool
import logging

from logging_setup import setup_logging
from task_data import chunks

logger = logging.getLogger(__name__)

@tool
def search_policy(keyword: str) -> str:
    """Return the policy chunks whose text contains the keyword, each tagged with its chunk id."""
    lines = []
    for c in chunks:
        if keyword.lower() in c["text"].lower():
            lines.append(f"[{c['chunk_id']}] {c['text']}")
    return "\n".join(lines)

def main() -> None:
    setup_logging()
    result = search_policy.invoke({"keyword": "30 days"})
    logger.info("tool results:\n%s", result)

if __name__ == "__main__":
    main()
