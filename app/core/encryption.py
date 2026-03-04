"""
Encryption service for sensitive device telemetry.
Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
"""
from cryptography.fernet import Fernet
from app.core.config import ENCRYPTION_KEY
import json
import logging

logger = logging.getLogger(__name__)

_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if not ENCRYPTION_KEY:
            raise RuntimeError("ENCRYPTION_KEY not set — cannot encrypt/decrypt data.")
        key = ENCRYPTION_KEY
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_payload(data: dict) -> str:
    """Encrypt a dict -> base64 Fernet token string."""
    f = _get_fernet()
    raw = json.dumps(data, default=str).encode("utf-8")
    return f.encrypt(raw).decode("utf-8")


def decrypt_payload(token: str) -> dict:
    """Decrypt a Fernet token string -> dict."""
    f = _get_fernet()
    raw = f.decrypt(token.encode("utf-8"))
    return json.loads(raw)
