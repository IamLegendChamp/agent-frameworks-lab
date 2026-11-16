import asyncio
import logging

from dotenv import load_dotenv

from a2a_lab.policy_caller import ask
from a2a_lab.security import a2a_token
from logging_setup import setup_logging
from mao_lab.runner import run_case
from mao_lab.tools import RefundLedger

logger = logging.getLogger(__name__)

A2A_URL = "http://127.0.0.1:9000"


async def a2a_lookup(keyword: str) -> str:
    """The policy worker's tool is another agent, reached over A2A with a signed card check and a bearer token."""
    return await ask(A2A_URL, keyword, a2a_token())


async def broken_lookup(keyword: str) -> str:
    """A policy agent that always answers with nothing, to show the hop limit stopping a loop."""
    return ""


CASES = [
    ("policy_question", "How many days do I have to return an unused item?", "", a2a_lookup, None),
    ("refund_approved", "Please refund my order.", "T-1001", a2a_lookup, "approve"),
    ("refund_rejected", "Please refund my order.", "T-1002", a2a_lookup, "reject"),
    ("loop_guard", "How many days do I have to return an item?", "", broken_lookup, None),
]


async def main() -> None:
    ledger = RefundLedger()
    for case_name, question, order_id, lookup, decision in CASES:
        logger.info("=== case=%s", case_name)
        outcome = await run_case(case_name, question, order_id, lookup, ledger, decision)
        logger.info("route_log:")
        for step in outcome.values["route_log"]:
            logger.info("  %s", step)
        logger.info("hops=%d", outcome.values["hops"])
        logger.info("status=%s", outcome.values["status"])
        logger.info("answer=%s", outcome.values["answer"])
    logger.info("refund calls total=%d", ledger.calls)
    logger.info("refunds issued=%d", len(ledger.issued))


if __name__ == "__main__":
    setup_logging()
    load_dotenv()
    asyncio.run(main())
