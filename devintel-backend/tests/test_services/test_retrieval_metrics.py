"""Tests for app.ai.evaluation.retrieval_metrics — pure math, hand-verified.

Every expected value below was computed by hand before writing the assertion.
"""

import pytest

from app.ai.evaluation.retrieval_metrics import (
    AggregateRetrievalMetrics,
    RetrievalMetrics,
    RetrievalResult,
    compute_hit_at_k,
    compute_mrr,
    compute_precision_at_k,
    compute_recall_at_k,
    evaluate_retrieval,
    evaluate_single_query,
)


# ---------------------------------------------------------------------------
# Fixtures: concrete retrieval scenarios
# ---------------------------------------------------------------------------

# Scenario: retrieved 5 files, 2 of which are relevant out of 3 expected.
#   Retrieved top-5: [A, B, C, D, E]
#   Expected:        [A, C, X]  (A and C are hits; X was missed)
RETRIEVED_5 = ["file_a.py", "file_b.py", "file_c.py", "file_d.py", "file_e.py"]
EXPECTED_3 = ["file_a.py", "file_c.py", "file_x.py"]

# Scenario: perfect retrieval — all expected files in the top-K
PERFECT_RETRIEVED = ["e1.py", "e2.py", "extra.py"]
PERFECT_EXPECTED = ["e1.py", "e2.py"]


# ======================================================================
# compute_recall_at_k
# ======================================================================

class TestRecallAtK:
    def test_partial_hit(self):
        # 2 of 3 expected found in top 5 → 2/3
        assert compute_recall_at_k(RETRIEVED_5, EXPECTED_3, k=5) == pytest.approx(2 / 3)

    def test_k_limits_retrieved(self):
        # k=2 → only [A, B] considered → A is in expected → 1/3
        assert compute_recall_at_k(RETRIEVED_5, EXPECTED_3, k=2) == pytest.approx(1 / 3)

    def test_no_hits(self):
        assert compute_recall_at_k(["z.py", "y.py"], EXPECTED_3, k=5) == 0.0

    def test_perfect(self):
        assert compute_recall_at_k(PERFECT_RETRIEVED, PERFECT_EXPECTED, k=3) == 1.0

    def test_empty_expected_no_retrieved(self):
        # Unanswerable: 0 expected, 0 retrieved → 1.0
        assert compute_recall_at_k([], [], k=5) == 1.0

    def test_empty_expected_with_retrieved(self):
        # Unanswerable: 0 expected but items retrieved → false-positive noise → 0.0
        assert compute_recall_at_k(["noise.py"], [], k=5) == 0.0


# ======================================================================
# compute_precision_at_k
# ======================================================================

class TestPrecisionAtK:
    def test_partial_hit(self):
        # top 5: 2 hits out of 5 → 2/5 = 0.4
        assert compute_precision_at_k(RETRIEVED_5, EXPECTED_3, k=5) == pytest.approx(0.4)

    def test_k_limits_retrieved(self):
        # k=2 → [A, B] → 1 hit (A) → 1/2 = 0.5
        assert compute_precision_at_k(RETRIEVED_5, EXPECTED_3, k=2) == pytest.approx(0.5)

    def test_perfect(self):
        # k=2 → [e1, e2] → both relevant → 2/2 = 1.0
        assert compute_precision_at_k(PERFECT_RETRIEVED, PERFECT_EXPECTED, k=2) == 1.0

    def test_k_zero_no_expected(self):
        # k=0 and no expected → 1.0
        assert compute_precision_at_k([], [], k=0) == 1.0

    def test_k_zero_with_expected(self):
        # k=0 but expected is non-empty → 0.0
        assert compute_precision_at_k(RETRIEVED_5, EXPECTED_3, k=0) == 0.0

    def test_empty_retrieved_no_expected(self):
        # No items retrieved, no expected → 1.0
        assert compute_precision_at_k([], [], k=5) == 1.0

    def test_no_hits(self):
        assert compute_precision_at_k(["z.py"], EXPECTED_3, k=5) == pytest.approx(0.0)

    def test_empty_expected_with_retrieved(self):
        # 0 expected, stuff retrieved → 0.0
        assert compute_precision_at_k(["noise.py"], [], k=5) == 0.0


# ======================================================================
# compute_mrr
# ======================================================================

class TestMRR:
    def test_first_hit_at_rank_1(self):
        # A is relevant and at rank 1 → MRR = 1/1 = 1.0
        assert compute_mrr(RETRIEVED_5, EXPECTED_3) == 1.0

    def test_first_hit_at_rank_3(self):
        # Expected = [file_c.py] → first relevant at rank 3 → 1/3
        assert compute_mrr(RETRIEVED_5, ["file_c.py"]) == pytest.approx(1 / 3)

    def test_no_hit(self):
        assert compute_mrr(["z.py", "y.py"], EXPECTED_3) == 0.0

    def test_empty_expected_no_retrieved(self):
        # Unanswerable, correctly suppressed → 1.0
        assert compute_mrr([], []) == 1.0

    def test_empty_expected_with_retrieved(self):
        assert compute_mrr(["noise.py"], []) == 0.0


# ======================================================================
# compute_hit_at_k
# ======================================================================

class TestHitAtK:
    def test_hit_exists(self):
        # At least 1 relevant file in top 5 → 1.0
        assert compute_hit_at_k(RETRIEVED_5, EXPECTED_3, k=5) == 1.0

    def test_hit_at_smaller_k(self):
        # k=1 → [A] → A is relevant → 1.0
        assert compute_hit_at_k(RETRIEVED_5, EXPECTED_3, k=1) == 1.0

    def test_no_hit(self):
        assert compute_hit_at_k(["z.py", "y.py"], EXPECTED_3, k=5) == 0.0

    def test_miss_at_small_k(self):
        # k=1 → [B] → B not in expected → 0.0
        assert compute_hit_at_k(["file_b.py"], EXPECTED_3, k=1) == 0.0

    def test_empty_expected_no_retrieved(self):
        assert compute_hit_at_k([], [], k=5) == 1.0

    def test_empty_expected_with_retrieved(self):
        assert compute_hit_at_k(["noise.py"], [], k=5) == 0.0


# ======================================================================
# evaluate_single_query
# ======================================================================

class TestEvaluateSingleQuery:
    def test_returns_correct_dataclass(self):
        result = RetrievalResult(
            query_id="q1",
            retrieved_files=RETRIEVED_5,
            expected_files=EXPECTED_3,
        )
        metrics = evaluate_single_query(result, k=5)

        assert isinstance(metrics, RetrievalMetrics)
        assert metrics.query_id == "q1"
        assert metrics.k == 5
        assert metrics.recall_at_k == pytest.approx(2 / 3)
        assert metrics.precision_at_k == pytest.approx(0.4)
        assert metrics.mrr == 1.0          # A is at rank 1
        assert metrics.hit_at_k == 1.0

    def test_custom_k(self):
        result = RetrievalResult(
            query_id="q2",
            retrieved_files=RETRIEVED_5,
            expected_files=["file_c.py"],
        )
        metrics = evaluate_single_query(result, k=2)

        # k=2 → [A, B] → neither is file_c → all zero except MRR
        assert metrics.recall_at_k == 0.0
        assert metrics.precision_at_k == 0.0
        assert metrics.hit_at_k == 0.0
        # MRR considers full list → file_c at rank 3 → 1/3
        assert metrics.mrr == pytest.approx(1 / 3)


# ======================================================================
# evaluate_retrieval (aggregate)
# ======================================================================

class TestEvaluateRetrieval:
    def test_empty_results(self):
        agg = evaluate_retrieval([], k=5)
        assert isinstance(agg, AggregateRetrievalMetrics)
        assert agg.total_queries == 0
        assert agg.mean_recall_at_k == 0.0

    def test_aggregate_two_queries(self):
        r1 = RetrievalResult("q1", RETRIEVED_5, EXPECTED_3)          # recall@5=2/3
        r2 = RetrievalResult("q2", PERFECT_RETRIEVED, PERFECT_EXPECTED)  # recall@3=1.0

        agg = evaluate_retrieval([r1, r2], k=5)

        assert agg.total_queries == 2
        assert agg.total_expected_files == 5  # 3 + 2
        assert agg.total_files_found == 4     # 2 (from r1) + 2 (from r2)
        # mean recall = (2/3 + 1.0) / 2 = 5/6
        assert agg.mean_recall_at_k == pytest.approx(5 / 6)
        assert len(agg.per_query) == 2
