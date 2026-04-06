from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_cipher() -> Fernet:
    if not settings.google_token_encryption_key:
        raise ValueError("GOOGLE_TOKEN_ENCRYPTION_KEY is not configured")
    return Fernet(settings.google_token_encryption_key.encode())


def encrypt_secret(value: str) -> str:
    return _get_cipher().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _get_cipher().decrypt(value.encode()).decode()
