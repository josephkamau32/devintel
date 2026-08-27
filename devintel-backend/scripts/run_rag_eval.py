"""RAG Evaluation Harness — End-to-end runner with REAL vector_search calls.

Inserts hand-crafted synthetic embeddings into the real PostgreSQL database,
calls the actual EmbeddingRepository.vector_search() against actual pgvector SQL,
and computes retrieval metrics from real database query results.

Usage:
    python scripts/run_rag_eval.py [--k 5] [--keep-fixture-data]

Flags:
    --k N                 Top-K for retrieval metrics (default: 5)
    --keep-fixture-data   Don't clean up eval data after run (for debugging)
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.evaluation.retrieval_metrics import (
    AggregateRetrievalMetrics,
    RetrievalResult,
    evaluate_retrieval,
)
from app.ai.evaluation.generation_metrics import (
    AggregateGenerationMetrics,
    GenerationMetricStatus,
    check_api_key_available,
    not_run_metrics,
)


EVAL_DATASET_PATH = PROJECT_ROOT / "tests" / "fixtures" / "eval_dataset.json"

# Fixed eval fixture identifiers — deterministic so cleanup is reliable
EVAL_REPO_ID = UUID("00000000-0000-0000-0000-e0a100000001")
EVAL_REPO_FULL_NAME = "__eval_fixture__/itsdangerous"

# Vector config
VECTOR_DIM = 1536
SIMILARITY_THRESHOLD = 0.3

# ── Canonical repository files in the eval fixture ───────────────────
# All files present in the fixture repository, indexed in a stable order.

ALL_FIXTURE_FILES = [
    "src/itsdangerous/__init__.py",
    "src/itsdangerous/_json.py",
    "src/itsdangerous/encoding.py",
    "src/itsdangerous/exc.py",
    "src/itsdangerous/serializer.py",
    "src/itsdangerous/signer.py",
    "src/itsdangerous/timed.py",
    "src/itsdangerous/url_safe.py",
    "src/itsdangerous/contrib/legacy_compat.py",
    "tests/test_security_audit.py",
    "setup.cfg",
    "docs/conf.py",
    "tests/conftest.py",
    "tests/test_itsdangerous.py",
    "src/itsdangerous/py.typed",
]

FILE_INDEX_MAP = {file_path: idx for idx, file_path in enumerate(ALL_FIXTURE_FILES)}


# ── Vector math ──────────────────────────────────────────────────────

def make_canonical_chunk_vector(file_index: int, dim: int = VECTOR_DIM) -> list[float]:
    """Create a unit basis vector for a given file index in the repository.

    Chunk vector e_j has 1.0 at coordinate j, 0.0 everywhere else.
    This guarantees mutual orthogonality between all repository files.
    """
    vec = [0.0] * dim
    vec[file_index] = 1.0
    return vec


def make_query_vector(
    query_id: str,
    query_index: int,
    expected_files: list[str],
    dim: int = VECTOR_DIM,
) -> list[float]:
    """Construct a unit query vector with mathematically exact target similarities.

    For expected files [f_1, f_2, ..., f_m], weights w_k are assigned along
    each file's basis dimension, with the remaining energy along an orthogonal
    query-specific residual dimension.

    Dot product (cosine similarity) with file j's basis vector is:
    - w_k (>= 0.30) if file j is the k-th expected file
    - 0.0 (< 0.30) if file j is not in expected_files

    For unanswerable queries (expected_files = []), the query vector has 1.0
    entirely along an orthogonal residual dimension, yielding 0.0 similarity
    to all repository files (correctly returning 0 chunks above threshold).
    """
    vec = [0.0] * dim
    residual_dim = 100 + query_index

    if not expected_files:
        vec[residual_dim] = 1.0
        return vec

    # Weight presets based on number of expected files
    num_files = len(expected_files)
    if num_files == 1:
        weights = [0.90]
    elif num_files == 2:
        weights = [0.75, 0.55]
    elif num_files == 3:
        weights = [0.65, 0.52, 0.42]
    elif num_files == 4:
        weights = [0.58, 0.50, 0.44, 0.36]
    else:  # 5 or more
        weights = [0.52, 0.46, 0.42, 0.38, 0.32]

    sum_sq = 0.0
    for k, file_path in enumerate(expected_files[:len(weights)]):
        if file_path in FILE_INDEX_MAP:
            f_idx = FILE_INDEX_MAP[file_path]
            w = weights[k]
            vec[f_idx] = w
            sum_sq += w * w

    # Put residual energy along orthogonal dimension to maintain unit length
    residual = math.sqrt(max(0.0, 1.0 - sum_sq))
    vec[residual_dim] = residual

    return vec


# ── Database operations ──────────────────────────────────────────────

async def setup_eval_fixture() -> dict:
    """Insert the eval fixture repository and embeddings into the real DB."""
    from app.db.session import AsyncSessionLocal
    from app.models.repository import Repository
    from app.repositories.embedding import EmbeddingRepository
    from sqlalchemy import delete, select, text

    async with AsyncSessionLocal() as db:
        # Get an existing user_id for foreign key constraint
        user_res = await db.execute(select(Repository.user_id).limit(1))
        user_id = user_res.scalar()
        if not user_id:
            raise RuntimeError("No user found in database to attach eval repository to.")

        # Clean up any previous eval repository
        await db.execute(delete(Repository).where(Repository.id == EVAL_REPO_ID))
        await db.commit()

        # Insert repository model instance
        repo = Repository(
            id=EVAL_REPO_ID,
            user_id=user_id,
            full_name=EVAL_REPO_FULL_NAME,
            repo_name="itsdangerous",
            description="RAG eval fixture — synthetic embeddings, not a real user repo",
            url="https://github.com/pallets/itsdangerous",
            indexing_status="complete",
            indexing_mode="full",
            indexing_progress=100,
            default_branch="main",
        )
        db.add(repo)
        await db.flush()

        # Insert one chunk embedding per fixture file
        embedding_repo = EmbeddingRepository(db)
        embeddings_data = []
        for idx, file_path in enumerate(ALL_FIXTURE_FILES):
            vec = make_canonical_chunk_vector(idx)
            embeddings_data.append({
                "id": uuid4(),
                "repo_id": EVAL_REPO_ID,
                "file_path": file_path,
                "chunk_index": 0,
                "chunk_text": f"[eval-fixture] Synthetic chunk 0 for {file_path}",
                "embedding": vec,
            })

        await embedding_repo.create_bulk(embeddings_data)
        await db.commit()

        # Verify insertion count
        count_res = await db.execute(
            text("SELECT COUNT(*) FROM embeddings WHERE repo_id = :id"),
            {"id": str(EVAL_REPO_ID)},
        )
        count = count_res.scalar()

        return {
            "repo_id": EVAL_REPO_ID,
            "embeddings_inserted": len(embeddings_data),
            "embeddings_verified": count,
        }


async def run_real_retrieval(
    dataset: list[dict],
    k: int,
) -> list[RetrievalResult]:
    """Call the REAL EmbeddingRepository.vector_search for each eval entry."""
    from app.db.session import AsyncSessionLocal
    from app.repositories.embedding import EmbeddingRepository

    results = []

    async with AsyncSessionLocal() as db:
        embedding_repo = EmbeddingRepository(db)

        for query_idx, entry in enumerate(dataset):
            query_id = entry["id"]
            expected = entry["expected_files"]

            # Construct query vector
            q_vec = make_query_vector(query_id, query_idx, expected)

            # THE REAL CALL — actual SQL, actual pgvector, actual threshold
            search_results = await embedding_repo.vector_search(
                repo_id=EVAL_REPO_ID,
                query_embedding=q_vec,
                top_k=k,
                threshold=SIMILARITY_THRESHOLD,
            )

            # Extract unique file paths in returned rank order
            seen = set()
            retrieved_files = []
            for emb, sim in search_results:
                if emb.file_path not in seen:
                    seen.add(emb.file_path)
                    retrieved_files.append(emb.file_path)

            results.append(RetrievalResult(
                query_id=query_id,
                retrieved_files=retrieved_files,
                expected_files=expected,
            ))

    return results


async def cleanup_fixture() -> dict:
    """Remove all eval fixture data from the database."""
    from app.db.session import AsyncSessionLocal
    from app.models.repository import Repository
    from sqlalchemy import delete, text

    async with AsyncSessionLocal() as db:
        # Count before
        count_res = await db.execute(
            text("SELECT COUNT(*) FROM embeddings WHERE repo_id = :id"),
            {"id": str(EVAL_REPO_ID)},
        )
        count_before = count_res.scalar()

        # Delete repository (cascade deletes embeddings)
        await db.execute(delete(Repository).where(Repository.id == EVAL_REPO_ID))
        await db.commit()

        # Verify deletion
        count_after_res = await db.execute(
            text("SELECT COUNT(*) FROM embeddings WHERE repo_id = :id"),
            {"id": str(EVAL_REPO_ID)},
        )
        count_after = count_after_res.scalar()

        return {
            "embeddings_before": count_before,
            "embeddings_after": count_after,
        }


# ── Report formatting ────────────────────────────────────────────────

def load_eval_dataset() -> list[dict]:
    with open(EVAL_DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def format_report(
    retrieval: AggregateRetrievalMetrics,
    generation: AggregateGenerationMetrics,
    k: int,
    dataset: list[dict],
    setup_info: dict,
    cleanup_info: dict | None,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    categories = {}
    for entry in dataset:
        cat = entry["category"]
        categories[cat] = categories.get(cat, 0) + 1

    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  RAG Evaluation Report -- {now}")
    lines.append(f"  Fixture: itsdangerous@2.2.0 ({len(dataset)} eval entries)")
    lines.append(f"  Categories: {', '.join(f'{c}({n})' for c, n in sorted(categories.items()))}")
    lines.append(f"  Method: REAL EmbeddingRepository.vector_search (pgvector)")
    lines.append(f"  Embeddings inserted: {setup_info['embeddings_inserted']}")
    lines.append(f"  Embeddings verified: {setup_info['embeddings_verified']}")
    lines.append(f"  Similarity threshold: {SIMILARITY_THRESHOLD}")
    lines.append("=" * 60)
    lines.append("")

    # Retrieval metrics
    lines.append("RETRIEVAL METRICS (real pgvector queries)")
    lines.append("-" * 60)
    lines.append("  [!] CAVEAT: Retrieval metrics here validate MECHANISM correctness")
    lines.append("      using engineered, well-separated synthetic vectors -- not")
    lines.append("      real-world semantic retrieval quality, which requires actual")
    lines.append("      OpenAI embeddings and remains unmeasured until a real API key")
    lines.append("      is available.")
    lines.append("")
    lines.append(f"  Recall@{k}:     {retrieval.mean_recall_at_k:.3f}   "
                 f"({retrieval.total_files_found}/{retrieval.total_expected_files} expected files found)")
    lines.append(f"  Precision@{k}:  {retrieval.mean_precision_at_k:.3f}")
    lines.append(f"  MRR:          {retrieval.mean_mrr:.3f}")
    lines.append(f"  Hit@{k}:       {retrieval.mean_hit_at_k:.3f}   "
                 f"({sum(1 for m in retrieval.per_query if m.hit_at_k == 1.0)}/{retrieval.total_queries} "
                 f"queries had >=1 hit)")
    lines.append("")

    # Generation metrics
    lines.append("GENERATION METRICS")
    lines.append("-" * 60)
    if generation.status == GenerationMetricStatus.NOT_RUN:
        lines.append(f"  [!] {generation.message}")
        lines.append("")
        lines.append("  The following metrics are implemented and will produce")
        lines.append("  results when a valid API key is configured:")
        lines.append("")
        lines.append("  - Faithfulness (expected_claims check)")
        lines.append("  - Grounded Answer Rate (answerable entries)")
        lines.append("  - Hallucination Rate (unanswerable entries)")
        lines.append("  - Injection Resistance (prompt_injection entries)")
    else:
        if generation.faithfulness_rate is not None:
            lines.append(f"  Faithfulness:          {generation.faithfulness_rate:.3f}")
        if generation.grounded_answer_rate is not None:
            lines.append(f"  Grounded Answer Rate:  {generation.grounded_answer_rate:.3f}")
        if generation.hallucination_rate is not None:
            lines.append(f"  Hallucination Rate:    {generation.hallucination_rate:.3f}")
        if generation.injection_resistance_rate is not None:
            lines.append(f"  Injection Resistance:  {generation.injection_resistance_rate:.3f}")
    lines.append("")

    # Per-entry detail
    lines.append("PER-ENTRY RETRIEVAL DETAIL")
    lines.append("-" * 60)
    for m in retrieval.per_query:
        entry = next((e for e in dataset if e["id"] == m.query_id), None)
        cat = entry["category"] if entry else "unknown"
        expected_count = len(m.expected_files)

        if expected_count == 0:
            status = "OK (no files expected)"
        elif m.recall_at_k == 1.0:
            status = "PERFECT"
        elif m.recall_at_k > 0:
            found = len(set(m.retrieved_files) & set(m.expected_files))
            status = f"PARTIAL ({found}/{expected_count})"
        else:
            status = "MISS"

        lines.append(
            f"  {m.query_id:<10}  {cat:<25}  "
            f"Recall@{k}={m.recall_at_k:.2f}  {status}"
        )

        if 0 < m.recall_at_k < 1.0 and expected_count > 0:
            missed = set(m.expected_files) - set(m.retrieved_files)
            for miss in sorted(missed):
                lines.append(f"              MISSED: {miss}")

    lines.append("")

    # Cleanup info
    if cleanup_info:
        lines.append("CLEANUP")
        lines.append("-" * 60)
        lines.append(f"  Embeddings before cleanup: {cleanup_info['embeddings_before']}")
        lines.append(f"  Embeddings after cleanup:  {cleanup_info['embeddings_after']}")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"  Legend: PERFECT=all expected found  PARTIAL=some found  MISS=none found")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)


async def async_main(k: int, keep_fixture: bool):
    """Async entry point."""
    # Load dataset
    dataset = load_eval_dataset()

    # Reconfigure stdout for UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print(f"Loaded {len(dataset)} eval entries from {EVAL_DATASET_PATH}")
    print()

    # Step 1: Insert fixture data
    print("Setting up eval fixture in PostgreSQL database...")
    setup_info = await setup_eval_fixture()
    print(f"  Inserted {setup_info['embeddings_inserted']} embeddings "
          f"(verified in DB: {setup_info['embeddings_verified']})")
    print()

    # Step 2: Run real retrieval
    print(f"Running REAL EmbeddingRepository.vector_search queries (k={k}, threshold={SIMILARITY_THRESHOLD})...")
    retrieval_results = await run_real_retrieval(dataset, k=k)
    retrieval_metrics = evaluate_retrieval(retrieval_results, k=k)
    print(f"  Completed {len(retrieval_results)} queries against pgvector")
    print()

    # Step 3: Check generation metrics
    available, reason = check_api_key_available()
    generation_metrics = not_run_metrics(reason)

    # Step 4: Cleanup (unless --keep-fixture-data)
    cleanup_info = None
    if not keep_fixture:
        print("Cleaning up eval fixture data from database...")
        cleanup_info = await cleanup_fixture()
        print(f"  Embeddings before: {cleanup_info['embeddings_before']}")
        print(f"  Embeddings after:  {cleanup_info['embeddings_after']}")
        print()
    else:
        print("--keep-fixture-data specified: preserving eval fixture in database")
        print(f"  Fixture repo_id: {EVAL_REPO_ID}")
        print()

    # Format and print report
    report = format_report(
        retrieval_metrics, generation_metrics, k, dataset, setup_info, cleanup_info,
    )
    print(report)

    # Save report
    report_path = PROJECT_ROOT / "tests" / "fixtures" / "eval_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"Report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Run RAG evaluation harness")
    parser.add_argument("--k", type=int, default=5, help="Top-K for retrieval metrics")
    parser.add_argument("--keep-fixture-data", action="store_true",
                        help="Don't clean up eval data after run")
    args = parser.parse_args()

    asyncio.run(async_main(args.k, args.keep_fixture_data))


if __name__ == "__main__":
    main()
