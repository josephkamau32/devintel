"""Tests for JWT token creation, decoding, and backward compatibility with PyJWT."""

import base64
import hashlib
import hmac
import json
import time
from uuid import uuid4

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _generate_legacy_token(payload: dict, secret: str, algorithm: str = "HS256") -> str:
    """Generate a token manually using standard RFC 7519 / HS256 logic matching python-jose output."""
    header = {"typ": "JWT", "alg": algorithm}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def test_create_and_decode_access_token():
    user_id = uuid4()
    token = create_access_token(user_id)
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded == user_id


def test_create_and_decode_refresh_token():
    user_id = uuid4()
    token = create_refresh_token(user_id)
    assert isinstance(token, str)

    decoded = decode_refresh_token(token)
    assert decoded == user_id


def test_legacy_token_compatibility_hs256():
    """Verify that tokens generated with the old python-jose format decode seamlessly in PyJWT."""
    user_id = uuid4()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + 3600,  # 1 hour in future
    }
    legacy_token = _generate_legacy_token(payload, settings.JWT_SECRET_KEY, "HS256")

    # The new PyJWT-powered decode_access_token must decode it correctly
    decoded_id = decode_access_token(legacy_token)
    assert decoded_id == user_id, f"Expected {user_id}, got {decoded_id}"


def test_legacy_refresh_token_compatibility_hs256():
    """Verify that legacy refresh tokens decode seamlessly."""
    user_id = uuid4()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + 86400 * 7,
    }
    legacy_token = _generate_legacy_token(payload, settings.JWT_SECRET_KEY, "HS256")

    decoded_id = decode_refresh_token(legacy_token)
    assert decoded_id == user_id


def test_expired_token_returns_none():
    user_id = uuid4()
    now = int(time.time())
    expired_payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now - 3600,
        "exp": now - 60,  # 1 minute ago
    }
    expired_token = _generate_legacy_token(expired_payload, settings.JWT_SECRET_KEY, "HS256")
    assert decode_access_token(expired_token) is None


def test_invalid_signature_returns_none():
    user_id = uuid4()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + 3600,
    }
    tampered_token = _generate_legacy_token(payload, "wrong_secret_key_1234567890", "HS256")
    assert decode_access_token(tampered_token) is None


def test_wrong_type_token_returns_none():
    user_id = uuid4()
    token = create_refresh_token(user_id)
    # Passing refresh token to decode_access_token must return None
    assert decode_access_token(token) is None
