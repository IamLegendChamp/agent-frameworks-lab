import asyncio
import logging

from langchain.mcp import MCPAdapter
from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth
from dotenv import load_dotenv
from mcp_lab.idp import mint_token

from logging_setup import setup_logging

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:8000/mcp"


async def main():
    load_dotenv()
    client = Client(URL, auth=BearerAuth(mint_token()))
    async with MCPAdapter(client) as adapter:
        tools = await adapter.list_tools()
        logger.info("tool_count=%d", len(tools))
        for t in tools:
            logger.info("tool_name=%s", t.name)
            logger.info("tool_description=%s", t.description)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
