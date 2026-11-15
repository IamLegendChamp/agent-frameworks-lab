import logging
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware

from langchain_lab.policy_tools import search_policy
from logging_setup import setup_logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Trailpeak's support bot. Answer only from the policy text returned "
    "by the tool. If it has no relevant text, say you don't have that information. "
    "Be brief."
)

FALLBACK = "Sorry, I couldn't find that. A support agent will follow up."

def main() -> None:
    setup_logging()
    load_dotenv()
    llm = ChatGoogleGenerativeAI(model = os.environ["GEMINI_CHAT_MODEL"])
    agent = create_agent(
        llm, 
        [search_policy], 
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            ModelCallLimitMiddleware(run_limit=4),
            ToolCallLimitMiddleware(run_limit=2),
        ]
    )
    # logger.info("agent type: %s", type(agent).__name__)
    question = "How many days do I have to return an unused item?"
    # question = "Are you open on Sundays?"
    try:
        result = agent.invoke({"messages": [("user", question)]})
    except Exception as exc:
        logger.warning("agent failed: %s", type(exc).__name__)
        logger.info("final answer: %s", FALLBACK)
        return
    # logger.info("result keys: %s", list(result.keys()))
    for i, msg in enumerate(result["messages"]):
        logger.info("message %d", i)
        logger.info("  type: %s", type(msg).__name__)
        logger.info("  text: %r", msg.text)
        logger.info("  tool_calls: %s", getattr(msg, "tool_calls", None))
        logger.info("  finish_reason: %s", getattr(msg, "response_metadata", {}).get("finish_reason"))
    last = result["messages"][-1]
    finish = last.response_metadata.get("finish_reason")
    answer = last.text
    if not last.text or finish != "STOP":
        logger.warning("unsafe final message; finish_reason=%s", finish)
        answer = FALLBACK
    logger.info("message count: %d", len(result["messages"]))
    logger.info("final answer: %s", answer)

if __name__ == "__main__":
    main()
