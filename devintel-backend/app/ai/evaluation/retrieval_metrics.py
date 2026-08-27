"""Retrieval quality metrics for RAG evaluation.

Computes Recall@K, Precision@K, MRR, and Hit@K by comparing
retrieved file paths against ground-truth expected files.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrievalResult:
    """Result of a single retrieval query."""

    query_id: str
    retrieved_files: list[str]  # Ordered by rank (best first)
    expected_files: list[str]   # Ground-truth relevant files


@dataclass
class RetrievalMetrics:
    """Computed retrieval metrics for a single query."""

    query_id: str
    recall_at_k: float
    precision_at_k: float
    mrr: float
    hit_at_k: float
    k: int
    retrieved_files: list[str] = field(default_factory=list)
    expected_files: list[str] = field(default_factory=list)


@dataclass
class AggregateRetrievalMetrics:
    """Aggregated retrieval metrics across all queries."""

    mean_recall_at_k: float
    mean_precision_at_k: float
    mean_mrr: float
    mean_hit_at_k: float
    k: int
    total_queries: int
    total_expected_files: int
    total_files_found: int
    per_query: list[RetrievalMetrics] = field(default_factory=list)


def compute_recall_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    """Fraction of expected files that appear in the top-K retrieved results.

    Recall@K = |retrieved[:K] ∩ expected| / |expected|

    Special case for unanswerable queries (expected is empty):
    - Returns 1.0 if zero files retrieved (correctly suppressed).
    - Returns 0.0 if any files retrieved (false positive noise).
    """
    if not expected:
        return 1.0 if not retrieved[:k] else 0.0

    retrieved_set = set(retrieved[:k])
    hits = len(retrieved_set & set(expected))
    return hits / len(expected)


def compute_precision_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    """Fraction of top-K retrieved files that are in the expected set.

    Precision@K = |retrieved[:K] ∩ expected| / K

    Special case for unanswerable queries (expected is empty):
    - Returns 1.0 if zero files retrieved.
    - Returns 0.0 if any files retrieved.
    """
    if k == 0:
        return 1.0 if not expected else 0.0

    retrieved_top_k = retrieved[:k]
    if not retrieved_top_k:
        return 1.0 if not expected else 0.0

    if not expected:
        return 0.0

    hits = len(set(retrieved_top_k) & set(expected))
    return hits / k


def compute_mrr(retrieved: list[str], expected: list[str]) -> float:
    """Mean Reciprocal Rank: 1/rank of the first relevant file.

    MRR = 1 / rank_of_first_hit (1-indexed)

    Special case for unanswerable queries (expected is empty):
    - Returns 1.0 if zero files retrieved.
    - Returns 0.0 if any files retrieved.
    """
    if not expected:
        return 1.0 if not retrieved else 0.0

    expected_set = set(expected)
    for rank, file_path in enumerate(retrieved, start=1):
        if file_path in expected_set:
            return 1.0 / rank

    return 0.0


def compute_hit_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    """Binary hit: did any expected file appear in top-K?

    Hit@K = 1.0 if |retrieved[:K] ∩ expected| > 0, else 0.0

    Special case for unanswerable queries (expected is empty):
    - Returns 1.0 if zero files retrieved.
    - Returns 0.0 if any files retrieved.
    """
    if not expected:
        return 1.0 if not retrieved[:k] else 0.0

    retrieved_set = set(retrieved[:k])
    return 1.0 if (retrieved_set & set(expected)) else 0.0


def evaluate_single_query(result: RetrievalResult, k: int = 5) -> RetrievalMetrics:
    """Compute all retrieval metrics for a single query."""
    return RetrievalMetrics(
        query_id=result.query_id,
        recall_at_k=compute_recall_at_k(result.retrieved_files, result.expected_files, k),
        precision_at_k=compute_precision_at_k(result.retrieved_files, result.expected_files, k),
        mrr=compute_mrr(result.retrieved_files, result.expected_files),
        hit_at_k=compute_hit_at_k(result.retrieved_files, result.expected_files, k),
        k=k,
        retrieved_files=result.retrieved_files[:k],
        expected_files=result.expected_files,
    )


def evaluate_retrieval(results: list[RetrievalResult], k: int = 5) -> AggregateRetrievalMetrics:
    """Compute aggregate retrieval metrics across all queries."""
    if not results:
        return AggregateRetrievalMetrics(
            mean_recall_at_k=0.0,
            mean_precision_at_k=0.0,
            mean_mrr=0.0,
            mean_hit_at_k=0.0,
            k=k,
            total_queries=0,
            total_expected_files=0,
            total_files_found=0,
        )

    per_query = [evaluate_single_query(r, k) for r in results]

    total_expected = sum(len(r.expected_files) for r in results)
    total_found = sum(
        len(set(r.retrieved_files[:k]) & set(r.expected_files))
        for r in results
    )

    return AggregateRetrievalMetrics(
        mean_recall_at_k=sum(m.recall_at_k for m in per_query) / len(per_query),
        mean_precision_at_k=sum(m.precision_at_k for m in per_query) / len(per_query),
        mean_mrr=sum(m.mrr for m in per_query) / len(per_query),
        mean_hit_at_k=sum(m.hit_at_k for m in per_query) / len(per_query),
        k=k,
        total_queries=len(per_query),
        total_expected_files=total_expected,
        total_files_found=total_found,
        per_query=per_query,
    )
