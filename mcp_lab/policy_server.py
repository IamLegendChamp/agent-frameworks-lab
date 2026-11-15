import logging
import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware

from logging_setup import setup_logging
from task_data import chunks
from mcp_lab.idp import AUDIENCE, ISSUER, PUBLIC_PATH

logger = logging.getLogger(__name__)

verifier = JWTVerifier(
    public_key=PUBLIC_PATH.read_text(encoding="utf-8"),
    issuer=ISSUER,
    audience=AUDIENCE,
    required_scopes=["policy:read"]
)

ALLOWED_TOOLS = {"support-bot": {"search_policy"}}

class AuditAllowListMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        token = get_access_token()
        caller = token.client_id if token else "anonymous"
        tool = context.message.name
        allowed = tool in ALLOWED_TOOLS.get(caller, set())
        decision = "allow" if allowed else "deny"
        logger.info("audit caller=%s", caller)
        logger.info("audit tool=%s", tool)
        logger.info("audit arguments=%s", list((context.message.arguments or {}).keys()))
        logger.info("audit decision=%s", decision)
        if not allowed:
            raise ToolError(f"tool {tool} is not allowed for {caller}")
        return await call_next(context)

mcp = FastMCP("trailpeak_policy", auth=verifier, middleware=[AuditAllowListMiddleware()])


@mcp.tool
def search_policy(keyword: str) -> str:
    """Return the policy chunks whose text contains the keyword, each tagged with its chunk id."""
    lines = []
    for c in chunks:
        if keyword.lower() in c["text"].lower():
            lines.append(f"[{c['chunk_id']}] {c['text']}")
    logger.info("search_policy keyword=%r matches=%d", keyword, len(lines))
    return "\n".join(lines)


if __name__ == "__main__":
    setup_logging()
    mcp.run(transport="http", host="127.0.0.1", port=int(os.environ.get("MCP_PORT", 8000)))
