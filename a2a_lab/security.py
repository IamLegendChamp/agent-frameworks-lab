import logging

from fastmcp.server.auth.providers.jwt import JWTVerifier
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from mcp_lab.idp import ISSUER, PUBLIC_PATH, mint_token

logger = logging.getLogger(__name__)

# A token for the MCP server must NOT work here: each service accepts only its own audience.
A2A_AUDIENCE = "trailpeak-policy-a2a"
ALLOWED_CALLERS = {"support-bot"}
PUBLIC_PATHS = {"/.well-known/agent-card.json"}


def a2a_token(subject: str = "support-bot", expires_in_seconds: int = 300) -> str:
    """Stand-in for asking an identity provider for a token. Enterprise version: OAuth client-credentials grant."""
    return mint_token(
        subject=subject,
        audience=A2A_AUDIENCE,
        expires_in_seconds=expires_in_seconds,
    )


def build_verifier() -> JWTVerifier:
    """Needs only the public key. A missing key file stops the server (fail closed)."""
    return JWTVerifier(
        public_key=PUBLIC_PATH.read_text(encoding="utf-8"),
        issuer=ISSUER,
        audience=A2A_AUDIENCE,
        required_scopes=["policy:read"],
    )


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Checks the bearer token on every call except the public Agent Card, and writes one audit entry per call."""

    def __init__(self, app, verifier: JWTVerifier):
        super().__init__(app)
        self.verifier = verifier

    def _audit(self, caller: str, path: str, decision: str, reason: str) -> None:
        logger.info("audit caller=%s", caller)
        logger.info("audit path=%s", path)
        logger.info("audit decision=%s", decision)
        logger.info("audit reason=%s", reason)

    def _deny(self, caller: str, path: str, status: int, reason: str) -> JSONResponse:
        self._audit(caller, path, "deny", reason)
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else {}
        return JSONResponse({"error": reason}, status_code=status, headers=headers)

    async def dispatch(self, request, call_next):
        path = request.url.path
        if request.method == "GET" and path in PUBLIC_PATHS:
            return await call_next(request)
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            return self._deny("anonymous", path, 401, "missing bearer token")
        access = await self.verifier.verify_token(token)
        if access is None:
            return self._deny("unknown", path, 401, "invalid token")
        if access.client_id not in ALLOWED_CALLERS:
            return self._deny(access.client_id, path, 403, "caller not on allow-list")
        self._audit(access.client_id, path, "allow", "ok")
        return await call_next(request)
