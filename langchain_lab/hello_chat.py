import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from logging_setup import setup_logging
import os
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Answer(BaseModel):
    answer: str = Field(description="One short sentence answering the question")
    cited_chunk_ids: list[str] = Field(description="Source chunk ids such as C001; empty if no source")


def main() -> None:
    load_dotenv()
    setup_logging()
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
    llm = ChatGoogleGenerativeAI(
        model=os.environ["GEMINI_CHAT_MODEL"],
        timeout=timeout,
        max_retries=max_retries,
    )
    logger.info("model object created: %s", llm.model)
    messages = [
        SystemMessage(content="Answer in one short sentence."),
        HumanMessage(content="How many days do I have to return an unused item?"),
    ]
    plain_config = {
        "run_name": "hello_chat_plain",
        "tags": ["lab", "item-13"],
        "metadata": {"question_id": "G01"},
    }
    response = llm.invoke(messages, config=plain_config)
    logger.info("model said: %s", response.text)
    usage = response.usage_metadata
    logger.info("input tokens: %d", usage["input_tokens"])
    logger.info("output tokens: %d", usage["output_tokens"])
    logger.info("total tokens: %d", usage["total_tokens"])
    meta = response.response_metadata
    logger.info("metadata keys: %s", sorted(meta))
    logger.info("model name: %s", meta.get("model_name"))
    logger.info("finish reason: %s", meta.get("finish_reason"))
    structured_config = {
        "run_name": "hello_chat_structured",
        "tags": ["lab", "item-13"],
        "metadata": {"question_id": "G01"},
    }
    structured_llm = llm.with_structured_output(Answer)
    result = structured_llm.invoke(messages, config=structured_config)
    logger.info("structured answer: %s", result.answer)
    logger.info("cited chunk ids: %s", result.cited_chunk_ids)

if __name__ == "__main__":
    main()
