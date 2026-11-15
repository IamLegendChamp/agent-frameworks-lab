from pathlib import Path

from fastmcp.server.auth.providers.jwt import RSAKeyPair
from pydantic import SecretStr

KEY_DIR = Path(__file__).resolve().parent.parent / ".keys"
PRIVATE_PATH = KEY_DIR / "jwt_private.pem"
PUBLIC_PATH = KEY_DIR / "jwt_public.pem"

ISSUER = "https://idp.trailpeak.example"
AUDIENCE = "trailpeak-policy-mcp"


def ensure_keys() -> None:
    if PRIVATE_PATH.exists() and PUBLIC_PATH.exists():
        return
    pair = RSAKeyPair.generate()
    KEY_DIR.mkdir(exist_ok=True)
    PRIVATE_PATH.write_text(pair.private_key.get_secret_value(), encoding="utf-8", newline="\n")
    PUBLIC_PATH.write_text(pair.public_key, encoding="utf-8", newline="\n")


def mint_token(
    subject: str = "support-bot",
    audience: str = AUDIENCE,
    issuer: str = ISSUER,
    expires_in_seconds: int = 300,    
) -> str:
    ensure_keys()
    pair = RSAKeyPair(
        private_key=SecretStr(PRIVATE_PATH.read_text(encoding="utf-8")),
        public_key=PUBLIC_PATH.read_text(encoding="utf-8")
    )
    return pair.create_token(
        subject=subject,
        issuer=issuer,
        audience=audience,
        scopes=["policy:read"],
        expires_in_seconds=expires_in_seconds
    )


if __name__ == "__main__":
    ensure_keys()
    print("keys ready")
