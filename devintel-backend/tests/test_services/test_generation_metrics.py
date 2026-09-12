"""Tests for app.ai.evaluation.generation_metrics — generation quality metrics for RAG evaluation."""

import pytest

from app.ai.evaluation.generation_metrics import (
    AggregateGenerationMetrics,
    GenerationMetricStatus,
    GenerationResult,
    check_api_key_available,
    evaluate_faithfulness,
    evaluate_forbidden_claims,
    evaluate_generation,
    evaluate_single_generation,
    not_run_metrics,
)


# ======================================================================
# check_api_key_available
# ======================================================================

class TestCheckApiKeyAvailable:
    def test_missing_key_returns_false(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        is_avail, reason = check_api_key_available()
        assert is_avail is False
        assert "not set" in reason

    @pytest.mark.parametrize(
        "placeholder",
        [
            "sk-test-12345678901234567890",
            "sk-fake-key-placeholder-here",
            "sk-placeholder-long-enough-key",
            "test_key_12345678901234567890",
            "fake-key-12345678901234567890",
            "your-api-key-here-placeholder",
            "CHANGE_ME_NOW_PLEASE_12345",
            "xxxxxxxxxxxxxxxxxxxxxxxxx",
        ],
    )
    def test_placeholder_patterns_rejected(self, monkeypatch, placeholder):
        monkeypatch.setenv("OPENAI_API_KEY", placeholder)
        is_avail, reason = check_api_key_available()
        assert is_avail is False
        assert "placeholder pattern" in reason

    def test_short_key_rejected(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-shortkey")
        is_avail, reason = check_api_key_available()
        assert is_avail is False
        assert "too short" in reason

    def test_valid_looking_key_accepted(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "".join(["sk-", "validexamplekey12345678901234567890"]))
        is_avail, reason = check_api_key_available()
        assert is_avail is True
        assert "valid" in reason


# ======================================================================
# evaluate_faithfulness
# ======================================================================

class TestEvaluateFaithfulness:
    def test_all_expected_claims_found(self):
        response = "DevIntel uses FastAPI for the backend and React with Vite for the frontend."
        claims = ["FastAPI", "React", "Vite"]
        found, missing = evaluate_faithfulness(response, claims)
        assert found == ["FastAPI", "React", "Vite"]
        assert missing == []

    def test_partial_claims_found_and_missing(self):
        response = "The system uses PostgreSQL for storage."
        claims = ["PostgreSQL", "Redis cache", "Docker Compose"]
        found, missing = evaluate_faithfulness(response, claims)
        assert found == ["PostgreSQL"]
        assert missing == ["Redis cache", "Docker Compose"]

    def test_case_insensitive_matching(self):
        response = "authentication is handled by JWT bearer tokens."
        claims = ["JWT Bearer Tokens"]
        found, missing = evaluate_faithfulness(response, claims)
        assert len(found) == 1
        assert len(missing) == 0

    def test_delimited_phrase_matching(self):
        # Claim with comma delimiters: all key words present in response
        response = "The server supports python 3.11, fast execution, and strict typing."
        claims = ["python 3.11, fast execution; strict typing"]
        found, missing = evaluate_faithfulness(response, claims)
        assert len(found) == 1
        assert len(missing) == 0


# ======================================================================
# evaluate_forbidden_claims
# ======================================================================

class TestEvaluateForbiddenClaims:
    def test_no_forbidden_claims_present(self):
        response = "We use SQLAlchemy for database ORM."
        forbidden = ["MongoDB", "Django ORM"]
        violations = evaluate_forbidden_claims(response, forbidden)
        assert violations == []

    def test_forbidden_claim_detected(self):
        response = "The database is MongoDB running on port 27017."
        forbidden = ["MongoDB", "Cassandra"]
        violations = evaluate_forbidden_claims(response, forbidden)
        assert violations == ["MongoDB"]

    def test_skips_generic_meta_descriptions(self):
        response = "Any fabricated information should be prevented."
        forbidden = ["any fabricated data or endpoints"]
        violations = evaluate_forbidden_claims(response, forbidden)
        assert violations == []


# ======================================================================
# evaluate_single_generation
# ======================================================================

class TestEvaluateSingleGeneration:
    def test_answerable_query_passed(self):
        result = evaluate_single_generation(
            query_id="q1",
            category="architecture",
            answerable=True,
            response="DevIntel uses PostgreSQL with pgvector for vector search.",
            expected_claims=["PostgreSQL", "pgvector"],
            forbidden_claims=["MySQL"],
        )
        assert result.status == GenerationMetricStatus.PASSED
        assert result.expected_claims_found == ["PostgreSQL", "pgvector"]
        assert result.expected_claims_missing == []
        assert result.forbidden_claims_found == []

    def test_answerable_query_missing_claim_failed(self):
        result = evaluate_single_generation(
            query_id="q2",
            category="architecture",
            answerable=True,
            response="DevIntel uses PostgreSQL.",
            expected_claims=["PostgreSQL", "pgvector"],
            forbidden_claims=[],
        )
        assert result.status == GenerationMetricStatus.FAILED
        assert "pgvector" in result.expected_claims_missing

    def test_forbidden_claim_causes_failure_even_if_claims_present(self):
        result = evaluate_single_generation(
            query_id="q3",
            category="architecture",
            answerable=True,
            response="DevIntel uses PostgreSQL and MySQL.",
            expected_claims=["PostgreSQL"],
            forbidden_claims=["MySQL"],
        )
        assert result.status == GenerationMetricStatus.FAILED
        assert "MySQL" in result.forbidden_claims_found

    def test_unanswerable_query_correctly_refused(self):
        result = evaluate_single_generation(
            query_id="q4",
            category="unanswerable",
            answerable=False,
            response="I don't have information about blockchain integration in this repository.",
            expected_claims=[],
            forbidden_claims=[],
        )
        assert result.status == GenerationMetricStatus.PASSED
        assert "refused" in result.details.lower()

    def test_unanswerable_query_hallucinated_failed(self):
        result = evaluate_single_generation(
            query_id="q5",
            category="unanswerable",
            answerable=False,
            response="Blockchain integration is implemented in app/blockchain/solana.py with smart contracts.",
            expected_claims=[],
            forbidden_claims=[],
        )
        assert result.status == GenerationMetricStatus.FAILED
        assert "hallucination" in result.details.lower()


# ======================================================================
# evaluate_generation (aggregate) & not_run_metrics
# ======================================================================

class TestEvaluateGenerationAggregate:
    def test_empty_results_returns_not_run(self):
        agg = evaluate_generation([])
        assert agg.status == GenerationMetricStatus.NOT_RUN
        assert "No generation results" in agg.message

    def test_aggregate_metrics_computed_correctly(self):
        r1 = GenerationResult(
            query_id="q1",
            category="arch",
            answerable=True,
            status=GenerationMetricStatus.PASSED,
            expected_claims_found=["claim1"],
            expected_claims_missing=[],
        )
        r2 = GenerationResult(
            query_id="q2",
            category="arch",
            answerable=True,
            status=GenerationMetricStatus.FAILED,
            expected_claims_found=[],
            expected_claims_missing=["claim2"],
        )
        r3 = GenerationResult(
            query_id="q3",
            category="unanswerable",
            answerable=False,
            status=GenerationMetricStatus.FAILED,  # Hallucinated
        )
        r4 = GenerationResult(
            query_id="q4",
            category="prompt_injection",
            answerable=True,
            status=GenerationMetricStatus.PASSED,
            forbidden_claims_found=[],  # Resisted
        )

        agg = evaluate_generation([r1, r2, r3, r4])
        assert agg.status == GenerationMetricStatus.PASSED
        assert agg.total_queries == 4
        # Faithfulness: 2 of 3 answerable have no missing claims (r1 and r4) -> 2/3
        assert agg.faithfulness_rate == pytest.approx(2 / 3)
        # Grounded rate: 2 of 3 answerable passed (r1 and r4) -> 2/3
        assert agg.grounded_answer_rate == pytest.approx(2 / 3)
        # Hallucination rate: 1 of 1 unanswerable failed -> 1.0
        assert agg.hallucination_rate == 1.0
        # Injection resistance: 1 of 1 prompt_injection has no forbidden claims -> 1.0
        assert agg.injection_resistance_rate == 1.0

    def test_not_run_metrics_returns_proper_dataclass(self):
        metrics = not_run_metrics("Missing OPENAI_API_KEY")
        assert metrics.status == GenerationMetricStatus.NOT_RUN
        assert "Missing OPENAI_API_KEY" in metrics.message
