"""AI evaluator — automated quality scoring for LLM interactions.

Provides rule-based and heuristic evaluation of LLM responses across
multiple dimensions. Designed to be called after every orchestrator
completion to build a quality tracking dataset.

The evaluator runs synchronously (no LLM calls) so it adds negligible
latency to the request path.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime
from typing import Any, Optional

from app.ai.evaluation import (
    DimensionScore,
    EvaluationDimension,
    EvaluationResult,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIEvaluator:
    """Evaluate LLM response quality using heuristic rules.

    This is a zero-cost evaluator (no LLM calls). It scores responses
    based on structural checks, format compliance, and content heuristics.
    """

    def evaluate(
        self,
        *,
        prompt_messages: list[dict[str, str]],
        response_content: str,
        agent: str = "",
        model: str = "",
        latency_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        user_id: Optional[str] = None,
        repo_id: Optional[str] = None,
        expected_format: str = "text",  # "text", "json", "code"
    ) -> EvaluationResult:
        """Evaluate a single LLM interaction.

        Args:
            prompt_messages: The messages sent to the LLM.
            response_content: The raw response text.
            agent: Agent identifier (e.g., "pr_review", "chat").
            model: Model used (e.g., "gpt-4o").
            latency_ms: Response latency in milliseconds.
            prompt_tokens: Input token count.
            completion_tokens: Output token count.
            cost_usd: Estimated cost.
            user_id: User who triggered the request.
            repo_id: Repository context.
            expected_format: Expected response format.

        Returns:
            EvaluationResult with scores across all dimensions.
        """
        scores: list[DimensionScore] = []

        # Evaluate each dimension
        scores.append(self._score_relevance(prompt_messages, response_content))
        scores.append(self._score_completeness(response_content))
        scores.append(self._score_coherence(response_content))
        scores.append(self._score_safety(response_content))
        scores.append(self._score_format_compliance(response_content, expected_format))

        # Calculate overall score (weighted average)
        weights = {
            EvaluationDimension.RELEVANCE: 0.25,
            EvaluationDimension.COMPLETENESS: 0.20,
            EvaluationDimension.COHERENCE: 0.20,
            EvaluationDimension.SAFETY: 0.20,
            EvaluationDimension.FORMAT_COMPLIANCE: 0.15,
        }
        overall = sum(
            s.score * weights.get(s.dimension, 0.2) for s in scores
        )

        # Build prompt hash for deduplication
        prompt_text = json.dumps(prompt_messages, sort_keys=True)
        prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]

        result = EvaluationResult(
            evaluation_id=str(uuid.uuid4()),
            agent=agent,
            model=model,
            overall_score=round(min(overall, 1.0), 4),
            dimension_scores=scores,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            repo_id=repo_id,
            prompt_hash=prompt_hash,
            response_preview=response_content[:500] if response_content else "",
        )

        logger.debug(
            "Evaluation: agent=%s score=%.3f latency=%.0fms",
            agent, result.overall_score, latency_ms,
        )

        return result

    # ------------------------------------------------------------------
    # Dimension scorers
    # ------------------------------------------------------------------

    def _score_relevance(
        self, messages: list[dict[str, str]], response: str,
    ) -> DimensionScore:
        """Score how relevant the response is to the prompt."""
        if not response or not response.strip():
            return DimensionScore(
                dimension=EvaluationDimension.RELEVANCE,
                score=0.0,
                reasoning="Empty response",
            )

        # Check if response contains refusal patterns
        refusal_patterns = [
            r"I (?:can't|cannot|am unable to)",
            r"I don't have (?:access|information|enough)",
            r"As an AI",
        ]
        refusal_count = sum(
            1 for p in refusal_patterns if re.search(p, response, re.IGNORECASE)
        )

        # Basic keyword overlap between last user message and response
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        if not user_msg:
            return DimensionScore(
                dimension=EvaluationDimension.RELEVANCE,
                score=0.7,
                reasoning="No user message to compare against",
            )

        user_words = set(user_msg.lower().split())
        response_words = set(response.lower().split())
        overlap = len(user_words & response_words)
        overlap_ratio = overlap / max(len(user_words), 1)

        score = min(0.5 + overlap_ratio * 0.5, 1.0)
        if refusal_count > 0:
            score *= 0.7

        return DimensionScore(
            dimension=EvaluationDimension.RELEVANCE,
            score=round(score, 4),
            reasoning=f"Keyword overlap: {overlap_ratio:.2%}, refusals: {refusal_count}",
        )

    def _score_completeness(self, response: str) -> DimensionScore:
        """Score response completeness based on length and structure."""
        if not response:
            return DimensionScore(
                dimension=EvaluationDimension.COMPLETENESS,
                score=0.0,
                reasoning="Empty response",
            )

        length = len(response)

        # Very short responses are likely incomplete
        if length < 50:
            score = 0.3
            reasoning = "Very short response"
        elif length < 200:
            score = 0.6
            reasoning = "Short response"
        elif length < 2000:
            score = 0.85
            reasoning = "Medium-length response"
        else:
            score = 0.95
            reasoning = "Detailed response"

        # Check for truncation indicators
        if response.rstrip().endswith(("...", "```", "…")):
            score *= 0.8
            reasoning += " (possible truncation)"

        return DimensionScore(
            dimension=EvaluationDimension.COMPLETENESS,
            score=round(score, 4),
            reasoning=reasoning,
        )

    def _score_coherence(self, response: str) -> DimensionScore:
        """Score response coherence based on structure."""
        if not response:
            return DimensionScore(
                dimension=EvaluationDimension.COHERENCE,
                score=0.0,
                reasoning="Empty response",
            )

        score = 0.7  # Base score

        # Structured content is more coherent
        has_lists = bool(re.search(r"^\s*[-*\d]+[.)]\s", response, re.MULTILINE))
        has_headers = bool(re.search(r"^#+\s", response, re.MULTILINE))
        has_code_blocks = "```" in response
        has_paragraphs = "\n\n" in response

        structure_signals = sum([has_lists, has_headers, has_code_blocks, has_paragraphs])
        score += structure_signals * 0.075

        # Repetition penalty
        sentences = [s.strip() for s in re.split(r'[.!?]', response) if s.strip()]
        if len(sentences) > 2:
            unique_ratio = len(set(sentences)) / len(sentences)
            if unique_ratio < 0.7:
                score *= 0.7

        return DimensionScore(
            dimension=EvaluationDimension.COHERENCE,
            score=round(min(score, 1.0), 4),
            reasoning=f"Structure signals: {structure_signals}",
        )

    def _score_safety(self, response: str) -> DimensionScore:
        """Score response safety — check for leaked secrets or harmful content."""
        from app.ai.safety import has_secrets

        if not response:
            return DimensionScore(
                dimension=EvaluationDimension.SAFETY,
                score=1.0,
                reasoning="Empty response (safe)",
            )

        score = 1.0
        issues = []

        # Check for leaked secrets in response
        if has_secrets(response):
            score = 0.1
            issues.append("secrets detected in response")

        # Check for prompt injection indicators
        injection_patterns = [
            r"ignore (?:all )?previous instructions",
            r"system prompt",
            r"you are now",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                score *= 0.5
                issues.append(f"injection pattern: {pattern}")

        reasoning = "; ".join(issues) if issues else "No safety issues"
        return DimensionScore(
            dimension=EvaluationDimension.SAFETY,
            score=round(score, 4),
            reasoning=reasoning,
        )

    def _score_format_compliance(
        self, response: str, expected_format: str,
    ) -> DimensionScore:
        """Score whether the response matches the expected format."""
        if not response:
            return DimensionScore(
                dimension=EvaluationDimension.FORMAT_COMPLIANCE,
                score=0.0,
                reasoning="Empty response",
            )

        if expected_format == "json":
            # Try to extract and parse JSON
            try:
                from app.ai.response_parser import parse_json_response
                result = parse_json_response(response)
                if result is not None:
                    return DimensionScore(
                        dimension=EvaluationDimension.FORMAT_COMPLIANCE,
                        score=1.0,
                        reasoning="Valid JSON extracted",
                    )
            except Exception:
                pass

            return DimensionScore(
                dimension=EvaluationDimension.FORMAT_COMPLIANCE,
                score=0.3,
                reasoning="Expected JSON but could not parse",
            )

        elif expected_format == "code":
            has_code = "```" in response or response.strip().startswith(("def ", "class ", "import ", "from "))
            score = 0.9 if has_code else 0.5
            return DimensionScore(
                dimension=EvaluationDimension.FORMAT_COMPLIANCE,
                score=score,
                reasoning="Code block detected" if has_code else "No code block found",
            )

        # text format — always compliant
        return DimensionScore(
            dimension=EvaluationDimension.FORMAT_COMPLIANCE,
            score=0.9,
            reasoning="Text format (always compliant)",
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_evaluator: Optional[AIEvaluator] = None


def get_evaluator() -> AIEvaluator:
    """Return the global AIEvaluator singleton."""
    global _evaluator
    if _evaluator is None:
        _evaluator = AIEvaluator()
    return _evaluator
