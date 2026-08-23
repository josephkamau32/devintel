"""Webhook security — signature verification for GitHub webhooks.

GitHub signs webhook payloads with HMAC-SHA256 using the webhook secret.
This module verifies those signatures to prevent payload forgery.

Usage::

    from app.core.webhook import verify_github_signature

    is_valid = verify_github_signature(
        payload_body=request_body,
        signature_header=request.headers.get("X-Hub-Signature-256"),
        secret=settings.GITHUB_WEBHOOK_SECRET,
    )
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def verify_github_signature(
    payload_body: bytes,
    signature_header: Optional[str],
    secret: Optional[str] = None,
) -> bool:
    """Verify a GitHub webhook signature (HMAC-SHA256).

    Args:
        payload_body: Raw request body bytes.
        signature_header: Value of the ``X-Hub-Signature-256`` header.
        secret: Webhook secret. If None, uses ``settings.GITHUB_WEBHOOK_SECRET``.

    Returns:
        True if the signature is valid, False otherwise.

    Raises:
        RuntimeError: If the webhook secret is empty or unset (fail closed).
    """
    webhook_secret = secret if secret is not None else settings.GITHUB_WEBHOOK_SECRET
    if not webhook_secret:
        raise RuntimeError("GITHUB_WEBHOOK_SECRET is not configured.")

    if not signature_header:
        logger.warning("Webhook rejected: missing or empty X-Hub-Signature-256 header")
        return False

    # Expected format: "sha256=<hex_digest>"
    if not signature_header.startswith("sha256="):
        logger.warning("Webhook rejected: invalid signature format")
        return False

    expected_sig = signature_header[7:]  # Strip "sha256=" prefix

    # Compute HMAC-SHA256
    mac = hmac.new(
        webhook_secret.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    )
    computed_sig = mac.hexdigest()

    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(expected_sig, computed_sig)

    if not is_valid:
        logger.warning("Webhook rejected: signature mismatch")

    return is_valid
