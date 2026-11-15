import asyncio
import os
import socket
import subprocess
import sys
import time

import pytest
from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth
from fastmcp.server.auth.providers.jwt import RSAKeyPair
from langchain.mcp import MCPAdapter
from mcp.shared.exceptions import MCPError

from mcp_lab.idp import AUDIENCE, ISSUER, ensure_keys, mint_token

PORT = 8765
URL = f"http://127.0.0.1:{PORT}/mcp"


def wait_for_port(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.3)
    raise RuntimeError("policy server did not start")


@pytest.fixture(scope="module")
def server():
    ensure_keys()
    env = {**os.environ, "MCP_PORT": str(PORT)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_lab.policy_server"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_port(PORT)
        yield
    finally:
        proc.terminate()
        proc.wait(timeout=10)


async def list_tool_names(token: str) -> list[str]:
    client = Client(URL, auth=BearerAuth(token))
    async with MCPAdapter(client) as adapter:
        tools = await adapter.list_tools()
    return [t.name for t in tools]


async def call_search(token: str) -> str:
    client = Client(URL, auth=BearerAuth(token))
    async with client:
        result = await client.call_tool("search_policy", {"keyword": "return"})
    return str(result)


def forged_token() -> str:
    return RSAKeyPair.generate().create_token(
        subject="support-bot",
        issuer=ISSUER,
        audience=AUDIENCE,
        scopes=["policy:read"],
    )


BAD_TOKENS = {
    "expired": lambda: mint_token(expires_in_seconds=-60),
    "wrong_audience": lambda: mint_token(audience="some-other-service"),
    "wrong_issuer": lambda: mint_token(issuer="https://evil.example"),
    "forged_signature": forged_token,
}


def test_good_token_lists_the_tool(server):
    assert asyncio.run(list_tool_names(mint_token())) == ["search_policy"]


@pytest.mark.parametrize("name", list(BAD_TOKENS))
def test_bad_token_is_rejected(server, name):
    with pytest.raises(MCPError):
        asyncio.run(list_tool_names(BAD_TOKENS[name]()))


def test_allowed_caller_can_call_the_tool(server):
    assert "C001" in asyncio.run(call_search(mint_token()))


def test_unknown_caller_is_denied_by_allow_list(server):
    with pytest.raises(Exception, match="not allowed"):
        asyncio.run(call_search(mint_token(subject="intruder")))
