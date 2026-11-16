import logging
import operator
from collections.abc import Awaitable, Callable
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

logger = logging.getLogger(__name__)

MAX_HOPS = 6
FALLBACK = "Sorry, I couldn't complete that automatically. A support agent will follow up."

PolicyLookup = Callable[[str], Awaitable[str]]
RefundSender = Callable[[str, str], Awaitable[str]]


class State(TypedDict):
    question: str
    order_id: str
    hops: int
    route_log: Annotated[list[str], operator.add]
    policy_text: str
    refund_status: str
    receipt: str
    answer: str
    status: str


def initial_state(question: str, order_id: str = "") -> State:
    return {
        "question": question,
        "order_id": order_id,
        "hops": 0,
        "route_log": [],
        "policy_text": "",
        "refund_status": "none",
        "receipt": "",
        "answer": "",
        "status": "running",
    }


def keyword_for(question: str) -> str:
    return "refund" if "refund" in question.lower() else "return"


def wants_refund(state: State) -> bool:
    return "refund" in state["question"].lower() and bool(state["order_id"])


def build_graph(
    policy_lookup: PolicyLookup,
    refund_sender: RefundSender,
    checkpointer: BaseCheckpointSaver,
    max_hops: int = MAX_HOPS,
):
    """Supervisor and two workers. Hard limits live here in code, not in a prompt.

    Stand-in: the supervisor is a rule-based router. Enterprise version: a model chooses the route
    with structured output, and these same rules still enforce the hop limit and the approval gate.
    """

    def supervisor(state: State) -> Command[Literal["policy_worker", "refund_worker", "finish"]]:
        hop = state["hops"] + 1
        if hop > max_hops:
            logger.warning("supervisor hop limit reached")
            logger.warning("  hop=%d", hop)
            logger.warning("  max_hops=%d", max_hops)
            return Command(
                update={"hops": hop, "status": "hop_limit", "route_log": ["supervisor->finish(hop_limit)"]},
                goto="finish",
            )
        if not state["policy_text"]:
            target = "policy_worker"
        elif wants_refund(state) and state["refund_status"] == "none":
            target = "refund_worker"
        else:
            target = "finish"
        logger.info("supervisor routed")
        logger.info("  hop=%d", hop)
        logger.info("  target=%s", target)
        return Command(update={"hops": hop, "route_log": [f"supervisor->{target}"]}, goto=target)

    async def policy_worker(state: State) -> dict:
        keyword = keyword_for(state["question"])
        text = await policy_lookup(keyword)
        logger.info("policy_worker done")
        logger.info("  keyword=%s", keyword)
        logger.info("  chars=%d", len(text))
        return {"policy_text": text, "route_log": ["policy_worker"]}

    async def refund_worker(state: State) -> dict:
        # Nothing with a side effect may run before interrupt(): on resume this node starts again from the top.
        decision = interrupt(
            {
                "action": "issue_refund",
                "order_id": state["order_id"],
                "policy_excerpt": state["policy_text"][:200],
                "ask": "Reply approve or reject.",
            }
        )
        logger.info("refund_worker got decision")
        logger.info("  decision=%s", decision)
        if decision != "approve":
            return {"refund_status": "rejected", "route_log": ["refund_worker(rejected)"]}
        receipt = await refund_sender(state["order_id"], f"refund-{state['order_id']}")
        return {"refund_status": "issued", "receipt": receipt, "route_log": ["refund_worker(issued)"]}

    def finish(state: State) -> dict:
        if state["status"] == "hop_limit":
            answer, status = FALLBACK, "hop_limit"
        else:
            lines = state["policy_text"].splitlines()
            parts = [lines[0] if lines else "No policy text found."]
            if state["refund_status"] == "issued":
                parts.append(f"Your refund for order {state['order_id']} was approved (receipt {state['receipt']}).")
            elif state["refund_status"] == "rejected":
                parts.append(f"A reviewer declined the refund for order {state['order_id']}.")
            answer, status = " ".join(parts), "done"
        logger.info("finish")
        logger.info("  status=%s", status)
        return {"answer": answer, "status": status, "route_log": ["finish"]}

    builder = StateGraph(State)
    builder.add_node("supervisor", supervisor)
    builder.add_node("policy_worker", policy_worker)
    builder.add_node("refund_worker", refund_worker)
    builder.add_node("finish", finish)
    builder.add_edge(START, "supervisor")
    builder.add_edge("policy_worker", "supervisor")
    builder.add_edge("refund_worker", "supervisor")
    builder.add_edge("finish", END)
    return builder.compile(checkpointer=checkpointer)
