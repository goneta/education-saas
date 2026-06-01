import base64
import hashlib
import hmac
import os
import struct
import time
from urllib.parse import quote


def random_base32(length: int = 32) -> str:
    return base64.b32encode(os.urandom(length)).decode("ascii").replace("=", "")[:length]


def _hotp(secret: str, counter: int, digits: int = 6) -> str:
    key = base64.b32decode(secret.upper() + "=" * ((8 - len(secret) % 8) % 8))
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


def verify(secret: str, code: str, valid_window: int = 1, interval: int = 30) -> bool:
    cleaned = "".join(ch for ch in code if ch.isdigit())
    if len(cleaned) != 6:
        return False
    current_counter = int(time.time() // interval)
    for offset in range(-valid_window, valid_window + 1):
        if hmac.compare_digest(_hotp(secret, current_counter + offset), cleaned):
            return True
    return False


def provisioning_uri(secret: str, *, name: str, issuer_name: str) -> str:
    label = f"{quote(issuer_name)}:{quote(name)}"
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer_name)}&algorithm=SHA1&digits=6&period=30"
