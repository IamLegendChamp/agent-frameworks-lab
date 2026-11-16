import asyncio
import logging

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import get_message_text, new_text_message
from a2a.types.a2a_pb2 import Role, SendMessageRequest
from a2a.utils.signing import SignatureVerificationError, create_signature_verifier
from jwt.exceptions import InvalidKeyError

from a2a_lab.card_keys import ALGORITHM, KID, PUBLIC_PATH
from a2a_lab.security import a2a_token
from logging_setup import setup_logging

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:9000"
KEYWORD = "return"


def key_provider(kid: str | None, jku: str | None) -> bytes:
    """Return the public key for a key id we trust. Any other key id is refused.

    `jku` (a key-set URL named inside the card) is ignored on purpose: a card must not choose where we fetch keys.
    """
    if kid != KID:
        raise InvalidKeyError(f"unknown key id: {kid!r}")
    return PUBLIC_PATH.read_bytes()


verifier = create_signature_verifier(key_provider, algorithms=[ALGORITHM])


async def ask(url: str, keyword: str, token: str) -> str:
    """Fetch the card, verify its signature, then send one message with a bearer token. Returns the reply text."""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(headers=headers) as http:
        client = await create_client(
            url,
            client_config=ClientConfig(streaming=False, httpx_client=http),
            signature_verifier=verifier,
        )
        try:
            request = SendMessageRequest(message=new_text_message(keyword, role=Role.ROLE_USER))
            async for event in client.send_message(request):
                if event.HasField("message"):
                    return get_message_text(event.message)
            return ""
        finally:
            await client.close()


async def main() -> None:
    try:
        text = await ask(URL, KEYWORD, a2a_token())
    except SignatureVerificationError as exc:
        logger.warning("agent card REJECTED")
        logger.warning("  reason=%s", type(exc).__name__)
        return
    logger.info("agent card verified, reply received")
    logger.info("reply_text=%s", text)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
