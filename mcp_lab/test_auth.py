import asyncio
import base64
import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth
from fastmcp.server.auth.providers.jwt import RSAKeyPair
from fastmcp.exceptions import MCPError
from mcp_lab.idp import AUDIENCE, ISSUER, mint_token

logger = logging.getLogger(__name__)

LAB_ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_until_open(port: int, seconds: float = 15.0) -> None:
    deadline = time.time() + seconds
    attempt = 0
    logger.info("waiting_for_port=%d", port)
    logger.info("give_up_after_seconds=%.1f", seconds)
    logger.info("time.time()=%d", time.time())
    logger.info("deadline=%d", deadline)
    while time.time() < deadline:
        attempt += 1
        with socket.socket() as s:
            s.settimeout(0.5)
            result = s.connect_ex(("127.0.0.1", port))
            logger.info("attempt=%d", attempt)
            logger.info("connect_ex=%d", result)
            logger.info("seconds_left=%.1f", deadline - time.time())
            if result == 0:
                logger.info("port_open_after_attempts=%d", attempt)
                return
        time.sleep(0.2)
    logger.error("gave_up_after_attempts=%d", attempt)
    raise RuntimeError(f"Server did not open port {port}")


@pytest.fixture(scope="module")
def server_url(tmp_path_factory):
    port = free_port()
    log_path = tmp_path_factory.mktemp("server") / "server.log"
    log_file = open(log_path, "w", encoding="utf-8")
    env = {**os.environ, "MCP_PORT": str(port)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_lab.policy_server"],
        cwd=LAB_ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    logger.info("port=%d", port)
    try:
        wait_until_open(port)
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log_file.close()
        for line in log_path.read_text(encoding="utf-8").splitlines():
            logger.info("server| %s", line)


def log_claims(token: str) -> None:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    for key, value in claims.items():
        logger.info("claim %s=%s", key, value)


def list_tool_names(url: str, token: str) -> list[str]:
    async def run():
        async with Client(url, auth=BearerAuth(token)) as client:
            tools = await client.list_tools()
            names = [t.name for t in tools]
            logger.info("tools_found=%d", len(names))
            for name in names:
                logger.info("tool_name=%s", name)
            return names

    return asyncio.run(run())


def test_good_token_lists_search_policy(server_url):
    names = list_tool_names(server_url, mint_token())
    assert names == ["search_policy"]


def forged_token() -> str:
    rogue = RSAKeyPair.generate()
    return rogue.create_token(
        subject="support-bot", 
        issuer=ISSUER,
        audience=AUDIENCE,
        scopes=["policy:read"],
    )

@pytest.mark.parametrize(
    "label, make_token",
    [
        ("expired", lambda: mint_token(expires_in_seconds=-60)),
        ("wrong_audience", lambda: mint_token(audience="some-other-service")),
        ("wrong_issuer", lambda: mint_token(issuer="https://evil.example")),
        ("forged_signature", forged_token),
    ],
)

def test_bad_token_is_rejected(server_url, label, make_token):
    logger.info("case=%s", label)
    with pytest.raises(MCPError) as info:
        list_tool_names(server_url, make_token())
    logger.info("exc_type=%s", type(info.value).__name__)
