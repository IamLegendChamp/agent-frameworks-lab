import logging
import os
import json

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from langchain_lab.policy_tools import search_policy
from logging_setup import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    load_dotenv()
    llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_CHAT_MODEL"])
    llm_with_tools = llm.bind_tools([search_policy])
    schema = llm_with_tools.kwargs["tools"][0]["function"]
    # logger.info("bound tool:\n%s", json.dumps(schema, indent=2, default=str))
    messages = [
        SystemMessage(content="You are Trailpeak's support bot. Answer only from the policy text returned by the tool. If it has no relevant text, say you don't have that information. Be brief."),
        # HumanMessage(content="Are you open on Sundays?"),
        HumanMessage(content="How many days do I have to return an unused item?"),

    ]
    response = llm_with_tools.invoke(messages)
    # logger.info("tool calls:\n%s", json.dumps(response.tool_calls, indent=2, default=str))
    if not response.tool_calls:
        logger.warning("model made no tool call; answer: %s", response.text)
        return
    call = response.tool_calls[0]
    try:
        result = search_policy.invoke(call["args"])
    except Exception as exc:
        logger.warning("tool failed: %s", type(exc).__name__)
        result = f"Tool error: {type(exc).__name__}. Check the arguments and try again."
    if not result:
        result = "No policy text matched this keyword."
    max_chars = 300
    if len(result) > max_chars:
        logger.warning("tool result cut from %d to %d chars", len(result), max_chars)
        result = result[:max_chars] + "\n[truncated]"
    logger.info("tool results:\n%s", result)
    messages.append(response)
    messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
    final = llm.invoke(messages)
    answer = final.text
    if not final.text:
        logger.warning("model returned empty text; using fallback")
        answer = "Sorry, I couldn't find that. A support agent will follow up."
    logger.info("final text: %r", final.text)
    logger.info("final content: %r", final.content)
    logger.info("finish reason: %s", final.response_metadata.get("finish_reason"))
    logger.info("final answer: %s", answer)


if __name__ == "__main__":
    main()
