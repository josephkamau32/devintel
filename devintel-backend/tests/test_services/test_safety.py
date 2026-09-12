"""Tests for app.ai.safety — secret detection and redaction for LLM context.

Tests both positive detection (real secret shapes with fake values) and
negative detection (normal code/text avoiding false positives).
"""

import pytest

from app.ai.safety import detect_secrets, has_secrets, sanitize_for_llm

# Sample fake secret strings matching regex patterns in app/ai/safety.py
AWS_KEY = "".join(["AKIA", "IOSFODNN7EXAMPLE"])  # AKIA + 16 chars
AWS_SECRET = "aws_secret_access_key = " + "'" + "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" + "'"
GITHUB_TOKEN = "".join(["ghp_", "123456789012345678901234567890123456"])  # ghp_ + 36 chars
OPENAI_KEY = "".join(["sk-", "abcdef12345678901234567890123456"])  # sk- + 32 chars
GOOGLE_KEY = "AIzaSyD" + "A" * 32  # AIza + 35 chars
STRIPE_KEY = "".join(["sk_", "test_", "123456789012345678901234"])  # sk_test_ + 24 chars
GENERIC_PASSWORD = 'password = "super_secret_password_999"'
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
DATABASE_URL = "postgres://postgres:mypassword@localhost:5432/mydb"
PRIVATE_KEY_HEADER = "-----BEGIN RSA PRIVATE KEY-----"


# Normal code/text samples that should NOT trigger secret detection
CLEAN_PYTHON_CODE = """
def calculate_tax(subtotal: float, rate: float = 0.08) -> float:
    \"\"\"Calculate total sales tax for a given line item.\"\"\"
    if subtotal < 0:
        raise ValueError("Subtotal cannot be negative")
    return round(subtotal * rate, 2)
"""

CLEAN_DOCUMENTATION = """
DevIntel Architecture Overview
The platform connects to GitHub repositories, computes embeddings, and provides
chat and PR review capabilities using a retrieval-augmented generation pipeline.
"""


# ======================================================================
# has_secrets
# ======================================================================

class TestHasSecrets:
    @pytest.mark.parametrize(
        "secret_snippet, expected_type",
        [
            (f"export AWS_ACCESS_KEY_ID={AWS_KEY}", "AWS Access Key"),
            (AWS_SECRET, "AWS Secret Key"),
            (f"GITHUB_TOKEN = '{GITHUB_TOKEN}'", "GitHub Token"),
            (f"api_key = '{OPENAI_KEY}'", "OpenAI API Key"),
            (f"GOOGLE_API_KEY={GOOGLE_KEY}", "Google API Key"),
            (f"STRIPE_API_KEY = '{STRIPE_KEY}'", "Stripe Key"),
            (GENERIC_PASSWORD, "Generic Secret"),
            (f"Authorization: {BEARER_TOKEN}", "Bearer Token"),
            (f"DATABASE_URL={DATABASE_URL}", "Database URL"),
            (PRIVATE_KEY_HEADER, "Private Key"),
        ],
    )
    def test_detects_known_secret_shapes(self, secret_snippet, expected_type):
        assert has_secrets(secret_snippet) is True, f"Failed to detect {expected_type}"

    def test_clean_python_code_returns_false(self):
        assert has_secrets(CLEAN_PYTHON_CODE) is False

    def test_clean_documentation_returns_false(self):
        assert has_secrets(CLEAN_DOCUMENTATION) is False

    def test_empty_string_returns_false(self):
        assert has_secrets("") is False

    def test_short_generic_key_variable_not_flagged(self):
        # Normal dictionary key access shouldn't trigger generic secret regex
        # which requires value >= 8 chars and assignment syntax
        snippet = "key = 'short'"
        assert has_secrets(snippet) is False


# ======================================================================
# detect_secrets
# ======================================================================

class TestDetectSecrets:
    def test_single_secret_returns_type_and_count(self):
        snippet = f"Connect using token: {GITHUB_TOKEN}"
        detected = detect_secrets(snippet)
        assert len(detected) >= 1
        types = [d["type"] for d in detected]
        assert "GitHub Token" in types
        gh_entry = next(d for d in detected if d["type"] == "GitHub Token")
        assert gh_entry["count"] == "1"

    def test_multiple_occurrences_counted_accurately(self):
        # Two OpenAI keys in one snippet
        key1 = "".join(["sk-", "1" * 32])
        key2 = "".join(["sk-", "2" * 32])
        snippet = f"primary={key1}\nbackup={key2}"
        detected = detect_secrets(snippet)
        openai_entry = next(d for d in detected if d["type"] == "OpenAI API Key")
        assert openai_entry["count"] == "2"

    def test_clean_text_returns_empty_list(self):
        assert detect_secrets(CLEAN_PYTHON_CODE) == []


# ======================================================================
# sanitize_for_llm
# ======================================================================

class TestSanitizeForLLM:
    def test_redacts_single_secret_with_default_placeholder(self):
        snippet = f"API_KEY = '{OPENAI_KEY}'"
        sanitized = sanitize_for_llm(snippet)
        assert OPENAI_KEY not in sanitized
        assert "[REDACTED]" in sanitized

    def test_redacts_with_custom_marker(self):
        snippet = f"export AWS_ACCESS_KEY_ID={AWS_KEY}"
        custom_marker = "===SECRET_REMOVED==="
        sanitized = sanitize_for_llm(snippet, redaction_marker=custom_marker)
        assert AWS_KEY not in sanitized
        assert custom_marker in sanitized

    def test_redacts_multiple_different_secrets(self):
        snippet = f"AWS={AWS_KEY}\nOPENAI={OPENAI_KEY}\nDB={DATABASE_URL}"
        sanitized = sanitize_for_llm(snippet)
        assert AWS_KEY not in sanitized
        assert OPENAI_KEY not in sanitized
        assert DATABASE_URL not in sanitized
        assert sanitized.count("[REDACTED]") >= 3

    def test_clean_code_remains_unchanged(self):
        sanitized = sanitize_for_llm(CLEAN_PYTHON_CODE)
        assert sanitized == CLEAN_PYTHON_CODE

    def test_empty_string_returns_empty_string(self):
        assert sanitize_for_llm("") == ""

    def test_log_detections_disabled_does_not_fail(self):
        snippet = f"token: {GITHUB_TOKEN}"
        sanitized = sanitize_for_llm(snippet, log_detections=False)
        assert GITHUB_TOKEN not in sanitized
        assert "[REDACTED]" in sanitized
