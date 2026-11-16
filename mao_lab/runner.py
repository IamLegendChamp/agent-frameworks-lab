import logging
import uuid
from dataclasses import dataclass

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from mao_lab.graph import MAX_HOPS, PolicyLookup, build_graph, initial_state
from mao_lab.tools import RefundLedger

logger = logging.getLogger(__name__)


@dataclass
class Outcome:
    values: dict
    approval_request: dict | None


async def run_case(
    case_name: str,
    question: str,
    order_id: str,
    lookup: PolicyLookup,
    ledger: RefundLedger,
    decision: str | None,
    max_hops: int = MAX_HOPS,
) -> Outcome:
    """Run one customer case to the end, pausing at the approval gate if the graph asks for it.

    `decision` stands in for the human reviewer. None means nobody answered, so the run stays paused.
    Stand-in: InMemorySaver. Enterprise version: a Postgres checkpointer so a pause survives a restart.
    """
    graph = build_graph(lookup, ledger.issue, InMemorySaver(), max_hops=max_hops)
    config = {
        "configurable": {"thread_id": f"{case_name}-{uuid.uuid4()}"},
        "recursion_limit": 25,
        "run_name": "trailpeak_support_mao",
        "tags": ["f5", "mao"],
        "metadata": {"case": case_name},
    }
    await graph.ainvoke(initial_state(question, order_id), config)
    snapshot = await graph.aget_state(config)
    approval_request = None
    if snapshot.next and snapshot.interrupts:
        approval_request = snapshot.interrupts[0].value
        logger.info("approval requested")
        logger.info("  action=%s", approval_request["action"])
        logger.info("  order_id=%s", approval_request["order_id"])
        if decision is not None:
            await graph.ainvoke(Command(resume=decision), config)
            snapshot = await graph.aget_state(config)
    return Outcome(values=dict(snapshot.values), approval_request=approval_request)
