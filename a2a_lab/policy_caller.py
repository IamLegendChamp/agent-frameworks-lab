import asyncio
import logging

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import get_message_text, new_text_message
from a2a.types.a2a_pb2 import Role, SendMessageRequest

from logging_setup import setup_logging

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:9000"
KEYWORD = "return"


async def main() -> None:
    client = await create_client(URL, client_config=ClientConfig(streaming=False))
    try:
        request = SendMessageRequest(message=new_text_message(KEYWORD, role=Role.ROLE_USER))
        async for event in client.send_message(request):
            if event.HasField("message"):
                logger.info("reply_kind=message")
                logger.info("reply_text=%s", get_message_text(event.message))
            else:
                logger.info("reply_kind=other (not a plain message)")
    finally:
        await client.close()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
