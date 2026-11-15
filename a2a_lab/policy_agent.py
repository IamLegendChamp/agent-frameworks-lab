import logging

from a2a.helpers.proto_helpers import new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.utils.errors import UnsupportedOperationError

from task_data import chunks

logger = logging.getLogger(__name__)


def find_policy_text(keyword: str) -> str:
    lines = []
    for c in chunks:
        if keyword.lower() in c["text"].lower():
            lines.append(f"[{c['chunk_id']}] {c['text']}")
    return "\n".join(lines)


class PolicyExecutor(AgentExecutor):
    """The remote agent's brain: a keyword search over the policy chunks, no model call."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        keyword = context.get_user_input().strip()
        logger.info("a2a_request keyword=%r", keyword)
        text = find_policy_text(keyword) or "No policy text found for that keyword."
        logger.info("a2a_reply chars=%d", len(text))
        await event_queue.enqueue_event(new_text_message(text))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError("this agent answers at once and cannot be cancelled")
