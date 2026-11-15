import logging
import os

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types.a2a_pb2 import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import PROTOCOL_VERSION_1_0, TransportProtocol
from starlette.applications import Starlette

from a2a_lab.policy_agent import PolicyExecutor
from logging_setup import setup_logging

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = int(os.environ.get("A2A_PORT", "9000"))
BASE_URL = f"http://{HOST}:{PORT}/"


def build_card() -> AgentCard:
    return AgentCard(
        name="Trailpeak policy agent",
        description="Looks up Trailpeak return and refund policy text by keyword.",
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=BASE_URL,
                protocol_binding=TransportProtocol.JSONRPC.value,
                protocol_version=PROTOCOL_VERSION_1_0,
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="policy-lookup",
                name="Policy lookup",
                description="Send one keyword, get back the matching policy chunks with their ids.",
                tags=["policy", "returns", "refunds"],
                examples=["return", "refund"],
            )
        ],
    )


def build_app() -> Starlette:
    card = build_card()
    handler = DefaultRequestHandler(
        agent_executor=PolicyExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    return Starlette(routes=routes)


if __name__ == "__main__":
    setup_logging()
    logger.info("starting a2a policy agent")
    logger.info("  url=%s", BASE_URL)
    uvicorn.run(build_app(), host=HOST, port=PORT)
