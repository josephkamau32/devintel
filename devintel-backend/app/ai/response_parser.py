"""Reusable parser for extracting structured data from LLM responses.

This consolidates the duplicated JSON-parsing logic that was previously
scattered across pr_review_service.py, code_health_service.py,
auto_fix_service.py, and other services.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def parse_json_response(
    raw: str,
    *,
    fallback: Optional[dict[str, Any]] = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Extract a JSON object from a raw LLM response.

    Handles common LLM formatting quirks:
    1. Markdown code fences (```json ... ```)
    2. Leading/trailing whitespace
    3. JSON embedded within prose text
    4. Language specifier on the first line (e.g. ``json``)

    Args:
        raw: The raw string response from the LLM.
        fallback: Optional default dict to return if parsing fails.
            If None and parsing fails, raises ValueError.
        strict: If True, raise ValueError on parse failure even when
            fallback is provided.

    Returns:
        Parsed JSON as a Python dict.

    Raises:
        ValueError: If parsing fails and no fallback is provided (or strict=True).
    """
    content = _strip_code_fences(raw.strip())

    # Attempt 1: Direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Attempt 2: Find JSON boundaries
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

    # Attempt 3: Try to find a JSON array
    start = content.find("[")
    end = content.rfind("]") + 1
    if start != -1 and end > start:
        try:
            result = json.loads(content[start:end])
            if isinstance(result, list):
                return {"items": result}
        except json.JSONDecodeError:
            pass

    # All attempts failed
    if strict:
        raise ValueError(f"Failed to parse JSON from LLM response: {raw[:200]}")

    if fallback is not None:
        logger.warning("JSON parse failed, using fallback")
        return fallback

    raise ValueError(f"Failed to parse JSON from LLM response: {raw[:200]}")


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    if not text.startswith("```"):
        return text

    # Remove opening fence with optional language specifier
    text = re.sub(r"^```\w*\n?", "", text)

    # Remove closing fence
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def extract_multiple_json_blocks(raw: str) -> list[dict[str, Any]]:
    """Extract all JSON objects from a raw LLM response.

    Useful when the LLM returns multiple code-fenced JSON blocks.
    """
    blocks: list[dict[str, Any]] = []
    pattern = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)

    for match in pattern.finditer(raw):
        try:
            parsed = json.loads(match.group(1).strip())
            if isinstance(parsed, dict):
                blocks.append(parsed)
        except json.JSONDecodeError:
            continue

    # If no fenced blocks found, try the whole string
    if not blocks:
        try:
            result = parse_json_response(raw, strict=True)
            blocks.append(result)
        except ValueError:
            pass

    return blocks
