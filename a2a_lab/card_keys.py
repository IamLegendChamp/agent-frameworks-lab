from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

KEY_DIR = Path(__file__).resolve().parent.parent / ".keys"
PRIVATE_PATH = KEY_DIR / "card_private.pem"
PUBLIC_PATH = KEY_DIR / "card_public.pem"

KID = "trailpeak-card-key-1"
ALGORITHM = "RS256"


def ensure_card_keys() -> None:
    """Stand-in for a key service. Enterprise version: the private key lives in a KMS or HSM and the public key is published as a key set."""
    if PRIVATE_PATH.exists() and PUBLIC_PATH.exists():
        return
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    KEY_DIR.mkdir(exist_ok=True)
    PRIVATE_PATH.write_bytes(private_pem)
    PUBLIC_PATH.write_bytes(public_pem)


if __name__ == "__main__":
    ensure_card_keys()
    print("card keys ready")
