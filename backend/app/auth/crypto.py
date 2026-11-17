"""Optional Fernet encryption for sensitive fields (not passwords)."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import Settings, get_settings


def email_lookup_hash(email: str) -> str:
    normalized = email.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _fernet(settings: Settings | None = None) -> Fernet | None:
    settings = settings or get_settings()
    key = settings.data_encryption_key.strip()
    if not key:
        return None
    try:
        return Fernet(key.encode("utf-8"))
    except Exception:
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_field(plaintext: str, settings: Settings | None = None) -> str:
    f = _fernet(settings)
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_field(ciphertext: str, settings: Settings | None = None) -> str:
    f = _fernet(settings)
    if f is None:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ciphertext
