import asyncio
import logging

from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth
from fastmcp.server.auth.providers.jwt import RSAKeyPair
from langchain.mcp import MCPAdapter

from logging_setup import setup_logging
from mcp_lab.idp import AUDIENCE, ISSUER, mint_token

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:8000/mcp"


async def attempt(label: str, token: str) -> None:
    client = Client(URL, auth=BearerAuth(token))
    logger.info("case=%s", label)
    try:
        async with MCPAdapter(client) as adapter:
            tools = await adapter.list_tools()
        logger.info("  result=ACCEPTED tools=%d", len(tools))
    except Exception as exc:
        logger.info("  result=REJECTED (%s)", type(exc).__name__)


async def main() -> None:
    rogue = RSAKeyPair.generate()
    cases = [
        ("good token", mint_token()),
        ("expired token", mint_token(expires_in_seconds=-60)),
        ("wrong audience", mint_token(audience="some-other-service")),
        ("wrong issuer", mint_token(issuer="https://evil.example")),
        (
            "forged signature",
            rogue.create_token(
                subject="support-bot",
                issuer=ISSUER,
                audience=AUDIENCE,
                scopes=["policy:read"],
            ),
        ),
    ]
    for label, token in cases:
        await attempt(label, token)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
