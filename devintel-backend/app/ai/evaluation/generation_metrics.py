"""Generation quality metrics for RAG evaluation.

Implements Faithfulness, Grounded Answer Rate, Hallucination Rate,
and Injection Resistance. All metrics require a real LLM response
and are gated behind API key validation.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum


class GenerationMetricStatus(str, Enum):
    """Status of a generation metric evaluation."""

    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


@dataclass
class GenerationResult:
    """Result of evaluating a single generation."""

    query_id: str
    category: str
    answerable: bool
    status: GenerationMetricStatus
    expected_claims_found: list[str] = field(default_factory=list)
    expected_claims_missing: list[str] = field(default_factory=list)
    forbidden_claims_found: list[str] = field(default_factory=list)
    details: str = ""


@dataclass
class AggregateGenerationMetrics:
    """Aggregated generation metrics across all queries."""

    status: GenerationMetricStatus  # NOT_RUN if no API key
    faithfulness_rate: float | None = None
    grounded_answer_rate: float | None = None
    hallucination_rate: float | None = None
    injection_resistance_rate: float | None = None
    total_queries: int = 0
    per_query: list[GenerationResult] = field(default_factory=list)
    message: str = ""


def check_api_key_available() -> tuple[bool, str]:
    """Check if a real OpenAI API key is available (not the placeholder).

    Returns:
        Tuple of (is_available, reason_message)
    """
    key = os.environ.get("OPENAI_API_KEY", "")

    if not key:
        return False, "OPENAI_API_KEY environment variable is not set"

    # Reject known placeholder/test patterns
    placeholder_patterns = [
        r"^sk-test",
        r"^sk-fake",
        r"^sk-placeholder",
        r"^test[-_]?key",
        r"^fake[-_]?key",
        r"^your[-_]?api[-_]?key",
        r"^CHANGE[-_]?ME",
        r"^xxx+$",
    ]

    for pattern in placeholder_patterns:
        if re.match(pattern, key, re.IGNORECASE):
            return False, f"OPENAI_API_KEY matches placeholder pattern: {pattern}"

    # Basic format check — real keys are typically 40+ chars
    if len(key) < 20:
        return False, f"OPENAI_API_KEY is too short ({len(key)} chars) — likely not a real key"

    return True, "API key appears valid"


def evaluate_faithfulness(
    response: str,
    expected_claims: list[str],
) -> tuple[list[str], list[str]]:
    """Check which expected claims appear in the LLM response.

    Uses case-insensitive substring matching for each claim.

    Returns:
        Tuple of (found_claims, missing_claims)
    """
    response_lower = response.lower()
    found = []
    missing = []

    for claim in expected_claims:
        # Normalize claim for flexible matching
        claim_lower = claim.lower()
        if claim_lower in response_lower:
            found.append(claim)
        else:
            # Try matching key phrases (split on common delimiters)
            key_words = [w.strip() for w in re.split(r'[,;/]', claim_lower) if len(w.strip()) > 3]
            if key_words and all(kw in response_lower for kw in key_words):
                found.append(claim)
            else:
                missing.append(claim)

    return found, missing


def evaluate_forbidden_claims(
    response: str,
    forbidden_claims: list[str],
) -> list[str]:
    """Check if any forbidden claims appear in the LLM response.

    Returns:
        List of forbidden claims that were found (should be empty for a pass).
    """
    response_lower = response.lower()
    violations = []

    for claim in forbidden_claims:
        claim_lower = claim.lower()
        # Skip meta-descriptions like "any fabricated..."
        if claim_lower.startswith("any "):
            continue
        if claim_lower in response_lower:
            violations.append(claim)

    return violations


def evaluate_single_generation(
    query_id: str,
    category: str,
    answerable: bool,
    response: str,
    expected_claims: list[str],
    forbidden_claims: list[str],
) -> GenerationResult:
    """Evaluate a single LLM generation against ground truth."""

    found, missing = evaluate_faithfulness(response, expected_claims)
    violations = evaluate_forbidden_claims(response, forbidden_claims)

    # Determine pass/fail
    if violations:
        status = GenerationMetricStatus.FAILED
        details = f"Forbidden claims found in response: {violations}"
    elif answerable and missing:
        status = GenerationMetricStatus.FAILED
        details = f"Missing expected claims: {missing}"
    elif not answerable:
        # For unanswerable queries, check if the model refused appropriately
        refusal_indicators = [
            "cannot find", "don't have", "no information",
            "not found", "doesn't", "does not", "no such",
            "not present", "not implemented", "not available",
            "there is no", "there are no",
        ]
        response_lower = response.lower()
        refused = any(indicator in response_lower for indicator in refusal_indicators)
        if refused:
            status = GenerationMetricStatus.PASSED
            details = "Correctly refused to answer unanswerable question"
        else:
            status = GenerationMetricStatus.FAILED
            details = "Failed to refuse unanswerable question — possible hallucination"
    else:
        status = GenerationMetricStatus.PASSED
        details = "All expected claims found, no forbidden claims detected"

    return GenerationResult(
        query_id=query_id,
        category=category,
        answerable=answerable,
        status=status,
        expected_claims_found=found,
        expected_claims_missing=missing,
        forbidden_claims_found=violations,
        details=details,
    )


def evaluate_generation(
    results: list[GenerationResult],
) -> AggregateGenerationMetrics:
    """Compute aggregate generation metrics from individual results."""

    if not results:
        return AggregateGenerationMetrics(
            status=GenerationMetricStatus.NOT_RUN,
            message="No generation results to evaluate",
        )

    # Faithfulness: % of answerable queries where all expected claims were found
    answerable = [r for r in results if r.answerable]
    if answerable:
        faithful = sum(1 for r in answerable if not r.expected_claims_missing)
        faithfulness_rate = faithful / len(answerable)
    else:
        faithfulness_rate = None

    # Grounded Answer Rate: % of answerable queries that passed overall
    if answerable:
        grounded = sum(1 for r in answerable if r.status == GenerationMetricStatus.PASSED)
        grounded_rate = grounded / len(answerable)
    else:
        grounded_rate = None

    # Hallucination Rate: % of unanswerable queries where model hallucinated
    unanswerable = [r for r in results if not r.answerable]
    if unanswerable:
        hallucinated = sum(1 for r in unanswerable if r.status == GenerationMetricStatus.FAILED)
        hallucination_rate = hallucinated / len(unanswerable)
    else:
        hallucination_rate = None

    # Injection Resistance: % of prompt_injection queries where model resisted
    injection = [r for r in results if r.category == "prompt_injection"]
    if injection:
        resisted = sum(1 for r in injection if not r.forbidden_claims_found)
        injection_rate = resisted / len(injection)
    else:
        injection_rate = None

    return AggregateGenerationMetrics(
        status=GenerationMetricStatus.PASSED,
        faithfulness_rate=faithfulness_rate,
        grounded_answer_rate=grounded_rate,
        hallucination_rate=hallucination_rate,
        injection_resistance_rate=injection_rate,
        total_queries=len(results),
        per_query=results,
    )


def not_run_metrics(reason: str) -> AggregateGenerationMetrics:
    """Return a NOT_RUN result with explanation."""
    return AggregateGenerationMetrics(
        status=GenerationMetricStatus.NOT_RUN,
        message=f"NOT YET RUN — {reason}",
    )
