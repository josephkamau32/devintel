"""AI safety — secret detection and redaction for LLM context.

Prevents accidental leakage of secrets (API keys, tokens, passwords)
into AI prompts by scanning context text before sending to the provider.

Usage::

    from app.ai.safety import sanitize_for_llm

    safe_context = sanitize_for_llm(raw_code_context)
"""

from __future__ import annotations

import re
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Secret patterns
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    # API keys and tokens
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Key", re.compile(r"(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})")),
    ("GitHub Token", re.compile(r"gh[ps]_[A-Za-z0-9_]{36,}")),
    ("GitHub Fine-Grained Token", re.compile(r"github_pat_[A-Za-z0-9_]{22,}")),
    ("OpenAI API Key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("Anthropic API Key", re.compile(r"sk-ant-[A-Za-z0-9-]{80,}")),
    ("Slack Token", re.compile(r"xox[bprs]-[A-Za-z0-9-]{10,}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z-_]{35}")),
    ("Stripe Key", re.compile(r"[rs]k_(live|test)_[A-Za-z0-9]{24,}")),
    ("Heroku API Key", re.compile(r"(?i)heroku[_\-]?api[_\-]?key\s*[=:]\s*['\"]?[a-f0-9-]{36}")),

    # Generic secrets
    ("Private Key", re.compile(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----")),
    ("Generic Secret", re.compile(r"(?i)(?:secret|password|passwd|pwd|token|api_key|apikey|auth_token)\s*[=:]\s*['\"]([^'\"]{8,})['\"]")),
    ("Bearer Token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*")),
    ("Basic Auth", re.compile(r"Basic\s+[A-Za-z0-9+/=]{20,}")),

    # Database connection strings
    ("Database URL", re.compile(r"(?i)(?:postgres|mysql|mongodb|redis)://[^\s'\"]{10,}")),

    # JWT tokens
    ("JWT Token", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]

_REDACTION_PLACEHOLDER = "[REDACTED]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sanitize_for_llm(
    text: str,
    *,
    redaction_marker: str = _REDACTION_PLACEHOLDER,
    log_detections: bool = True,
) -> str:
    """Scan text for secrets and redact them before sending to an LLM.

    Args:
        text: Raw text (code context, diffs, etc.).
        redaction_marker: String to replace detected secrets with.
        log_detections: Whether to log detected secret types (not values).

    Returns:
        Sanitized text with secrets replaced.
    """
    if not text:
        return text

    detections: list[str] = []

    for name, pattern in _SECRET_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            detections.append(f"{name} ({len(matches)} occurrence(s))")
            text = pattern.sub(redaction_marker, text)

    if detections and log_detections:
        logger.warning(
            "Redacted %d secret type(s) from LLM context: %s",
            len(detections),
            ", ".join(detections),
        )

    return text


def detect_secrets(text: str) -> list[dict[str, str]]:
    """Detect (but don't redact) secrets in text.

    Returns:
        List of dicts with ``type`` and ``count`` for each detected secret type.
    """
    results = []
    for name, pattern in _SECRET_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            results.append({"type": name, "count": str(len(matches))})
    return results


def has_secrets(text: str) -> bool:
    """Quick check if text contains any detectable secrets."""
    for _, pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            return True
    return False
