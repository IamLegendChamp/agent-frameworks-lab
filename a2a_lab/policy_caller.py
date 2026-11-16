import asyncio
import logging

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import get_message_text, new_text_message
from a2a.types.a2a_pb2 import Role, SendMessageRequest
from a2a.utils.signing import SignatureVerificationError, create_signature_verifier
from jwt.exceptions import InvalidKeyError

from a2a_lab.card_keys import ALGORITHM, KID, PUBLIC_PATH
from logging_setup import setup_logging

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:9000"
KEYWORD = "return"


def key_provider(kid: str | None, jku: str | None) -> bytes:
    """Return the public key for a key id we trust. Any other key id is refused."""
    if kid != KID:
        raise InvalidKeyError(f"unknown key id: {kid!r}")
    return PUBLIC_PATH.read_bytes()


verifier = create_signature_verifier(key_provider, algorithms=[ALGORITHM])


async def main() -> None:
    try:
        client = await create_client(
            URL,
            client_config=ClientConfig(streaming=False),
            signature_verifier=verifier,
        )
    except SignatureVerificationError as exc:
        logger.warning("agent card REJECTED")
        logger.warning("  reason=%s", type(exc).__name__)
        return
    logger.info("agent card verified")
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
