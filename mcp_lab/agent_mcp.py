import asyncio
import logging
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain.mcp import MCPAdapter
from langchain_google_genai import ChatGoogleGenerativeAI
from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth
from mcp_lab.idp import mint_token

from logging_setup import setup_logging

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:8000/mcp"

SYSTEM_PROMPT = (
    "You are Trailpeak's support bot. Answer onlly from the policy text returned "
    "by the tool. If it has no relevant text, say you don't have that information. "
    "Be brief."
)

FALLBACK = "Sorry, I couldn't find that. A support agent will follow up."

async def main():
    load_dotenv()
    llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_CHAT_MODEL"])
    client = Client(URL, auth=BearerAuth(mint_token()))
    async with MCPAdapter(client) as adapter:
        tools = await adapter.list_tools()
        agent = create_agent(
            llm,
            tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=[
                ModelCallLimitMiddleware(run_limit=4),
                ToolCallLimitMiddleware(run_limit=2),
            ]
        )
        question="How many days do I have to return an unused item?"
        try:
            result = await agent.ainvoke({"messages": [("user", question)]})
        except Exception as exc:
            logger.warning("agent failed: %s", type(exc).__name__)
            logger.info("final answer: %s", FALLBACK)
            return
    for i, msg in enumerate(result["messages"]):
        logger.info("message %d", i)
        logger.info("  type: %s", type(msg).__name__)
        logger.info("  text: %r", msg.text)
        logger.info("  tool_calls: %s", getattr(msg, "tool_calls", None))
    last = result["messages"][-1]
    finish = last.response_metadata.get("finish_reason")
    answer = last.text
    if not last.text or finish != "STOP":
        logger.warning("unsafe final msg; finish_reason=%s", finish)
        answer = FALLBACK
    logger.info("message count: %d", len(result["messages"]))
    logger.info("final answer: %s", answer)

if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
