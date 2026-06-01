import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def _fernet() -> Optional[Fernet]:
    key = os.getenv("FIELD_ENCRYPTION_KEY")
    if not key:
        secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
        if not secret:
            return None
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest).decode("ascii")
    return Fernet(key.encode("ascii"))


def encrypt_secret(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    if value.startswith("enc:"):
        return value
    fernet = _fernet()
    if not fernet:
        return value
    return "enc:" + fernet.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    if not value or not value.startswith("enc:"):
        return value
    fernet = _fernet()
    if not fernet:
        return None
    try:
        return fernet.decrypt(value[4:].encode("ascii")).decode("utf-8")
    except InvalidToken:
        return None


def mask_secret(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    plain = decrypt_secret(value) or value
    if len(plain) <= 4:
        return "****"
    return f"{plain[:2]}****{plain[-2:]}"
