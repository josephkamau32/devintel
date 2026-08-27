"""Tests for retrieval metrics computation and real pipeline retrieval.

Divided into two explicit sections:
- Section A: Pure-arithmetic unit tests validating metric math in isolation
  (Recall@K, Precision@K, MRR, Hit@K against known hand-crafted inputs).
- Section B: Real end-to-end integration tests validating that
  EmbeddingRepository.vector_search against pgvector produces real scores
  and metrics as expected.
"""

from uuid import uuid4
import pytest
from sqlalchemy import delete, select

from app.ai.evaluation.retrieval_metrics import (
    RetrievalResult,
    compute_hit_at_k,
    compute_mrr,
    compute_precision_at_k,
    compute_recall_at_k,
    evaluate_retrieval,
    evaluate_single_query,
)
from app.db.session import AsyncSessionLocal
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository


# =====================================================================
# SECTION A: Metric Math in Isolation (Pure Unit Tests)
# =====================================================================

class TestRecallAtK:
    """Recall@K = |retrieved[:K] ∩ expected| / |expected|"""

    def test_perfect_recall(self):
        """All expected files are in the top-K results."""
        retrieved = ["a.py", "b.py", "c.py", "d.py", "e.py"]
        expected = ["a.py", "c.py"]
        assert compute_recall_at_k(retrieved, expected, k=5) == 1.0

    def test_partial_recall(self):
        """Only 1 of 2 expected files in top-K."""
        retrieved = ["a.py", "x.py", "y.py", "z.py", "w.py"]
        expected = ["a.py", "b.py"]
        assert compute_recall_at_k(retrieved, expected, k=5) == 0.5

    def test_zero_recall(self):
        """No expected files in top-K."""
        retrieved = ["x.py", "y.py", "z.py"]
        expected = ["a.py", "b.py"]
        assert compute_recall_at_k(retrieved, expected, k=3) == 0.0

    def test_k_truncation(self):
        """Expected file exists but beyond K."""
        retrieved = ["x.py", "y.py", "z.py", "a.py", "b.py"]
        expected = ["a.py"]
        # At k=3, a.py is at position 4 — not included
        assert compute_recall_at_k(retrieved, expected, k=3) == 0.0
        # At k=5, a.py is included
        assert compute_recall_at_k(retrieved, expected, k=5) == 1.0

    def test_empty_expected_with_zero_retrieved_passes(self):
        """Unanswerable query: expected=[], retrieved=[] -> 1.0 (pass, correctly suppressed)."""
        assert compute_recall_at_k([], [], k=5) == 1.0

    def test_empty_expected_with_retrieved_files_fails(self):
        """Unanswerable query: expected=[], retrieved=['a.py'] -> 0.0 (fail, false positive retrieval)."""
        assert compute_recall_at_k(["a.py", "b.py"], [], k=5) == 0.0

    def test_empty_retrieved(self):
        """Nothing retrieved but expected files exist -> 0."""
        assert compute_recall_at_k([], ["a.py"], k=5) == 0.0

    def test_three_of_four(self):
        """Exact fractional computation: 3/4 = 0.75."""
        retrieved = ["a.py", "b.py", "c.py", "x.py", "y.py"]
        expected = ["a.py", "b.py", "c.py", "d.py"]
        assert compute_recall_at_k(retrieved, expected, k=5) == 0.75


class TestPrecisionAtK:
    """Precision@K = |retrieved[:K] ∩ expected| / K"""

    def test_perfect_precision(self):
        """All K results are relevant."""
        retrieved = ["a.py", "b.py"]
        expected = ["a.py", "b.py", "c.py"]
        assert compute_precision_at_k(retrieved, expected, k=2) == 1.0

    def test_half_precision(self):
        """2 of 4 top-K are relevant -> 0.5."""
        retrieved = ["a.py", "x.py", "b.py", "y.py"]
        expected = ["a.py", "b.py"]
        assert compute_precision_at_k(retrieved, expected, k=4) == 0.5

    def test_zero_precision(self):
        """No relevant files in top-K."""
        retrieved = ["x.py", "y.py", "z.py"]
        expected = ["a.py", "b.py"]
        assert compute_precision_at_k(retrieved, expected, k=3) == 0.0

    def test_k_larger_than_retrieved(self):
        """K=5 but only 2 results. Precision = 2_hits / 5 = 0.4."""
        retrieved = ["a.py", "b.py"]
        expected = ["a.py", "b.py"]
        assert compute_precision_at_k(retrieved, expected, k=5) == 0.4

    def test_one_of_five(self):
        """1 relevant in 5 -> 0.2."""
        retrieved = ["x.py", "y.py", "a.py", "z.py", "w.py"]
        expected = ["a.py"]
        assert compute_precision_at_k(retrieved, expected, k=5) == 0.2


class TestMRR:
    """MRR = 1 / rank_of_first_relevant_file (1-indexed)"""

    def test_first_position(self):
        """First result is relevant -> MRR = 1.0."""
        assert compute_mrr(["a.py", "x.py", "y.py"], ["a.py"]) == 1.0

    def test_second_position(self):
        """First relevant at rank 2 -> MRR = 0.5."""
        assert compute_mrr(["x.py", "a.py", "y.py"], ["a.py"]) == 0.5

    def test_third_position(self):
        """First relevant at rank 3 -> MRR = 1/3."""
        assert compute_mrr(["x.py", "y.py", "a.py"], ["a.py"]) == pytest.approx(1 / 3)

    def test_no_relevant(self):
        """No relevant file found -> MRR = 0.0."""
        assert compute_mrr(["x.py", "y.py", "z.py"], ["a.py"]) == 0.0

    def test_multiple_expected_first_matters(self):
        """Multiple expected files — MRR uses rank of the FIRST one found."""
        retrieved = ["x.py", "b.py", "a.py"]
        expected = ["a.py", "b.py"]
        # b.py is at rank 2, a.py at rank 3 — first hit is b.py at rank 2
        assert compute_mrr(retrieved, expected) == 0.5

    def test_empty_expected_zero_retrieved_passes(self):
        """No expected, zero retrieved -> MRR = 1.0."""
        assert compute_mrr([], []) == 1.0

    def test_empty_expected_with_retrieved_fails(self):
        """No expected, but retrieved files -> MRR = 0.0."""
        assert compute_mrr(["a.py"], []) == 0.0


class TestHitAtK:
    """Hit@K = 1.0 if any expected file in top-K, else 0.0"""

    def test_hit(self):
        assert compute_hit_at_k(["x.py", "a.py", "y.py"], ["a.py"], k=5) == 1.0

    def test_miss(self):
        assert compute_hit_at_k(["x.py", "y.py", "z.py"], ["a.py"], k=5) == 0.0

    def test_hit_at_boundary(self):
        """File at exactly position K (1-indexed) -> hit."""
        assert compute_hit_at_k(["x.py", "y.py", "a.py"], ["a.py"], k=3) == 1.0

    def test_miss_beyond_k(self):
        """File at position K+1 -> miss."""
        assert compute_hit_at_k(["x.py", "y.py", "z.py", "a.py"], ["a.py"], k=3) == 0.0

    def test_empty_expected_zero_retrieved_passes(self):
        """No expected, zero retrieved -> Hit@K = 1.0."""
        assert compute_hit_at_k([], [], k=5) == 1.0

    def test_empty_expected_with_retrieved_fails(self):
        """No expected, but files retrieved -> Hit@K = 0.0."""
        assert compute_hit_at_k(["a.py"], [], k=5) == 0.0


class TestEvaluateSingleQuery:
    """Unit test for evaluate_single_query."""

    def test_perfect_result(self):
        result = RetrievalResult(
            query_id="q1",
            retrieved_files=["a.py", "b.py", "c.py"],
            expected_files=["a.py", "b.py"],
        )
        metrics = evaluate_single_query(result, k=5)
        assert metrics.recall_at_k == 1.0
        assert metrics.mrr == 1.0
        assert metrics.hit_at_k == 1.0

    def test_no_hits(self):
        result = RetrievalResult(
            query_id="q2",
            retrieved_files=["x.py", "y.py"],
            expected_files=["a.py"],
        )
        metrics = evaluate_single_query(result, k=5)
        assert metrics.recall_at_k == 0.0
        assert metrics.mrr == 0.0
        assert metrics.hit_at_k == 0.0

    def test_unanswerable_empty_expected_zero_retrieved_passes(self):
        """Unanswerable query with 0 retrieved files -> all metrics = 1.0."""
        result = RetrievalResult(
            query_id="q3",
            retrieved_files=[],
            expected_files=[],
        )
        metrics = evaluate_single_query(result, k=5)
        assert metrics.recall_at_k == 1.0
        assert metrics.precision_at_k == 1.0
        assert metrics.mrr == 1.0
        assert metrics.hit_at_k == 1.0

    def test_unanswerable_empty_expected_with_retrieved_fails(self):
        """Unanswerable query where pipeline retrieved noise -> all metrics = 0.0."""
        result = RetrievalResult(
            query_id="q4",
            retrieved_files=["x.py", "y.py"],
            expected_files=[],
        )
        metrics = evaluate_single_query(result, k=5)
        assert metrics.recall_at_k == 0.0
        assert metrics.precision_at_k == 0.0
        assert metrics.mrr == 0.0
        assert metrics.hit_at_k == 0.0


class TestEvaluateRetrieval:
    """Unit test for aggregate evaluation."""

    def test_aggregate_two_queries(self):
        results = [
            RetrievalResult("q1", ["a.py", "b.py"], ["a.py"]),
            RetrievalResult("q2", ["x.py", "y.py"], ["a.py"]),
        ]
        agg = evaluate_retrieval(results, k=5)
        assert agg.total_queries == 2
        # q1: recall=1.0, q2: recall=0.0 -> mean=0.5
        assert agg.mean_recall_at_k == 0.5
        assert agg.mean_mrr == 0.5
        assert agg.mean_hit_at_k == 0.5

    def test_empty_results(self):
        agg = evaluate_retrieval([], k=5)
        assert agg.total_queries == 0
        assert agg.mean_recall_at_k == 0.0

    def test_all_perfect(self):
        results = [
            RetrievalResult("q1", ["a.py"], ["a.py"]),
            RetrievalResult("q2", ["b.py"], ["b.py"]),
            RetrievalResult("q3", ["c.py", "d.py"], ["c.py", "d.py"]),
        ]
        agg = evaluate_retrieval(results, k=5)
        assert agg.mean_recall_at_k == 1.0
        assert agg.mean_mrr == 1.0
        assert agg.mean_hit_at_k == 1.0
        assert agg.total_files_found == 4
        assert agg.total_expected_files == 4


# =====================================================================
# SECTION B: Real End-to-End Retrieval Pipeline (pgvector DB Tests)
# =====================================================================

class TestRealDatabaseVectorSearch:
    """Tests that execute real EmbeddingRepository.vector_search against pgvector in PostgreSQL."""

    @pytest.mark.asyncio
    async def test_real_vector_search_exact_match(self):
        """Insert synthetic embeddings, query with pgvector, verify real cosine similarity."""
        try:
            async with AsyncSessionLocal() as db:
                user_res = await db.execute(select(Repository.user_id).limit(1))
                user_id = user_res.scalar()
                if not user_id:
                    pytest.skip("No user in database for test repository FK")
        except Exception as e:
            pytest.skip(f"Live PostgreSQL database not reachable on host: {e}")

        async with AsyncSessionLocal() as db:
            user_res = await db.execute(select(Repository.user_id).limit(1))
            user_id = user_res.scalar()
            test_repo_id = uuid4()
            repo = Repository(
                id=test_repo_id,
                user_id=user_id,
                full_name=f"__test__/vector_eval_{test_repo_id.hex[:8]}",
                repo_name="eval_test",
                url="https://github.com/pallets/itsdangerous",
                indexing_status="complete",
                indexing_mode="full",
            )
            db.add(repo)
            await db.flush()

            try:
                repo_obj = EmbeddingRepository(db)
                # Basis vector for signer.py
                v_signer = [1.0] + [0.0] * 1535
                # Basis vector for encoding.py
                v_encoding = [0.0, 1.0] + [0.0] * 1534

                await repo_obj.create_bulk([
                    {
                        "id": uuid4(),
                        "repo_id": test_repo_id,
                        "file_path": "src/itsdangerous/signer.py",
                        "chunk_index": 0,
                        "chunk_text": "Signer class implementation",
                        "embedding": v_signer,
                    },
                    {
                        "id": uuid4(),
                        "repo_id": test_repo_id,
                        "file_path": "src/itsdangerous/encoding.py",
                        "chunk_index": 0,
                        "chunk_text": "base64 encoding implementation",
                        "embedding": v_encoding,
                    },
                ])
                await db.commit()

                # Normalized query vector with 0.90 similarity to signer.py
                import math
                residual = math.sqrt(1.0 - 0.90 ** 2)  # ~0.4359
                query_vec = [0.90, 0.0, residual] + [0.0] * 1533
                results = await repo_obj.vector_search(
                    repo_id=test_repo_id,
                    query_embedding=query_vec,
                    top_k=5,
                    threshold=0.3,
                )

                # Expect 1 hit (signer.py above threshold 0.3, encoding.py is 0.0 < 0.3)
                assert len(results) == 1
                emb, sim = results[0]
                assert emb.file_path == "src/itsdangerous/signer.py"
                assert sim == pytest.approx(0.90, abs=0.01)

                # Verify metric calculation from real DB result
                retrieval_res = RetrievalResult(
                    query_id="eval-003",
                    retrieved_files=[emb.file_path for emb, _ in results],
                    expected_files=["src/itsdangerous/signer.py"],
                )
                m = evaluate_single_query(retrieval_res, k=5)
                assert m.recall_at_k == 1.0
                assert m.mrr == 1.0
                assert m.hit_at_k == 1.0

            finally:
                await db.execute(delete(Repository).where(Repository.id == test_repo_id))
                await db.commit()

    @pytest.mark.asyncio
    async def test_real_vector_search_unanswerable_threshold_filter(self):
        """Verify unanswerable queries return 0 chunks from pgvector when below threshold."""
        try:
            async with AsyncSessionLocal() as db:
                user_res = await db.execute(select(Repository.user_id).limit(1))
                user_id = user_res.scalar()
                if not user_id:
                    pytest.skip("No user in database for test repository FK")
        except Exception as e:
            pytest.skip(f"Live PostgreSQL database not reachable on host: {e}")

        async with AsyncSessionLocal() as db:
            user_res = await db.execute(select(Repository.user_id).limit(1))
            user_id = user_res.scalar()
            test_repo_id = uuid4()
            repo = Repository(
                id=test_repo_id,
                user_id=user_id,
                full_name=f"__test__/unanswerable_eval_{test_repo_id.hex[:8]}",
                repo_name="eval_test",
                url="https://github.com/pallets/itsdangerous",
                indexing_status="complete",
                indexing_mode="full",
            )
            db.add(repo)
            await db.flush()

            try:
                repo_obj = EmbeddingRepository(db)
                # Basis vector for signer.py
                v_signer = [1.0] + [0.0] * 1535

                await repo_obj.create_bulk([
                    {
                        "id": uuid4(),
                        "repo_id": test_repo_id,
                        "file_path": "src/itsdangerous/signer.py",
                        "chunk_index": 0,
                        "chunk_text": "Signer class implementation",
                        "embedding": v_signer,
                    }
                ])
                await db.commit()

                # Orthogonal query (similarity 0.0 < 0.3 threshold)
                query_vec = [0.0] * 100 + [1.0] + [0.0] * 1435
                results = await repo_obj.vector_search(
                    repo_id=test_repo_id,
                    query_embedding=query_vec,
                    top_k=5,
                    threshold=0.3,
                )

                # Should return empty results
                assert len(results) == 0

                # Metric calculation: unanswerable with 0 retrieved is a pass
                retrieval_res = RetrievalResult(
                    query_id="eval-011",
                    retrieved_files=[],
                    expected_files=[],
                )
                m = evaluate_single_query(retrieval_res, k=5)
                assert m.recall_at_k == 1.0
                assert m.mrr == 1.0
                assert m.hit_at_k == 1.0

            finally:
                await db.execute(delete(Repository).where(Repository.id == test_repo_id))
                await db.commit()
