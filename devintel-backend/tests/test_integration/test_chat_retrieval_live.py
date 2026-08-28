"""Live database integration test for the production chat retrieval path.

PURPOSE:
    This test exercises the REAL production call chain that users hit:

        ChatService.retrieve_relevant_chunks()
          → ContextPipeline.retrieve()
            → EmbeddingService.generate_embedding()  [mocked — returns list[float]]
            → EmbeddingRepository.vector_search()     [REAL — executes raw SQL via asyncpg]

    It inserts real embedding rows into PostgreSQL/pgvector, calls through the
    actual ChatService → ContextPipeline → EmbeddingRepository.vector_search
    code path, and verifies that the query embedding (a list[float]) is correctly
    handled all the way through to pgvector's cosine distance operator.

WHY THIS EXISTS:
    The existing test suite (test_services/test_chat.py, test_integration/test_rag_pipeline.py)
    fully mocks EmbeddingRepository.vector_search and/or uses SQLite, meaning the actual
    raw SQL text() query with asyncpg's type-conversion behavior was never exercised.
    This allowed a critical bug (asyncpg.DataError: expected str, got list) to ship
    undetected in the production chat retrieval path.

    This test ensures that class of bug — code that passes mocks but fails against a
    real asyncpg driver — cannot silently regress.

REQUIRES:
    Live PostgreSQL with pgvector extension, reachable at DATABASE_URL.
    Skips gracefully if the database is unreachable (e.g., CI without live Postgres,
    or Windows host port conflict with a native Postgres service).
"""

import math
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text

from app.db.session import AsyncSessionLocal
from app.models.embedding import Embedding
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.chat import ChatService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _probe_live_db():
    """Verify live PostgreSQL is reachable and return a valid user_id for FK."""
    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(Repository.user_id).limit(1))
        user_id = user_res.scalar()
        return user_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChatRetrievalLiveDB:
    """Integration tests that exercise the REAL production chat retrieval path
    against a live PostgreSQL/pgvector database.

    These tests intentionally DO NOT mock EmbeddingRepository or the DB session.
    The only mock is EmbeddingService.generate_embedding (to avoid needing a
    real OpenAI API key) and the cache (to avoid Redis dependency).
    """

    @pytest.mark.asyncio
    async def test_chat_service_retrieve_through_real_vector_search(self):
        """Full production path: ChatService → ContextPipeline → real vector_search.

        Proves that a list[float] query embedding flows correctly through the
        entire call chain and returns the expected chunk from pgvector.
        """
        # Gate: skip if live DB is unreachable
        try:
            user_id = await _probe_live_db()
            if not user_id:
                pytest.skip("No user in database for test repository FK")
        except Exception as e:
            pytest.skip(f"Live PostgreSQL database not reachable: {e}")

        test_repo_id = uuid4()

        async with AsyncSessionLocal() as db:
            # Setup: create test repository
            repo = Repository(
                id=test_repo_id,
                user_id=user_id,
                full_name=f"__test__/chat_retrieval_live_{test_repo_id.hex[:8]}",
                repo_name="chat_retrieval_live",
                url="https://github.com/test/chat_retrieval_live",
                indexing_status="complete",
                indexing_mode="full",
            )
            db.add(repo)
            await db.flush()

            try:
                embedding_repo = EmbeddingRepository(db)

                # Insert two embeddings with orthogonal basis vectors:
                #   signer.py  → [1, 0, 0, 0, ...]
                #   encoding.py → [0, 1, 0, 0, ...]
                v_signer = [1.0] + [0.0] * 1535
                v_encoding = [0.0, 1.0] + [0.0] * 1534

                await embedding_repo.create_bulk([
                    {
                        "id": uuid4(),
                        "repo_id": test_repo_id,
                        "file_path": "src/signer.py",
                        "chunk_index": 0,
                        "chunk_text": "class Signer: signs data using HMAC",
                        "embedding": v_signer,
                    },
                    {
                        "id": uuid4(),
                        "repo_id": test_repo_id,
                        "file_path": "src/encoding.py",
                        "chunk_index": 0,
                        "chunk_text": "base64 encoding utilities",
                        "embedding": v_encoding,
                    },
                ])
                await db.commit()

                # Build a query vector with high similarity to signer.py only
                # cos_sim(query, v_signer) ≈ 0.90
                # cos_sim(query, v_encoding) ≈ 0.0
                residual = math.sqrt(1.0 - 0.90 ** 2)
                query_vec = [0.90, 0.0, residual] + [0.0] * 1533

                # ---- Exercise the REAL production path ----
                # Mock only: embedding generation (no OpenAI key) and cache (no Redis)
                # NOT mocked: EmbeddingRepository, the DB session, vector_search SQL
                with patch("app.services.chat.EmbeddingService") as MockEmbSvc:
                    mock_emb_svc = MockEmbSvc.return_value
                    mock_emb_svc.generate_embedding = AsyncMock(return_value=query_vec)

                    chat_service = ChatService()
                    chat_service.embedding_service = mock_emb_svc

                    with patch("app.ai.context.pipeline.cache") as mock_cache:
                        mock_cache.get = AsyncMock(return_value=None)
                        mock_cache.set = AsyncMock()

                        results = await chat_service.retrieve_relevant_chunks(
                            repo_id=test_repo_id,
                            question="How does signing work?",
                            embedding_repo=embedding_repo,
                            top_k=5,
                            expand_context=False,  # Skip neighbor expansion for clean test
                        )

                # ---- Assertions ----
                # The call succeeded (no asyncpg DataError)
                assert results is not None, "retrieve_relevant_chunks returned None"
                assert len(results) >= 1, (
                    f"Expected at least 1 result from vector_search, got {len(results)}. "
                    "This would indicate the fix did not propagate to the real path."
                )

                # The correct chunk was retrieved
                file_paths = [emb.file_path for emb, _ in results]
                assert "src/signer.py" in file_paths, (
                    f"Expected src/signer.py in results, got: {file_paths}"
                )

                # Similarity score is approximately 0.90
                signer_results = [(emb, sim) for emb, sim in results if emb.file_path == "src/signer.py"]
                assert signer_results, "signer.py not in results"
                _, similarity = signer_results[0]
                assert abs(similarity - 0.90) < 0.02, (
                    f"Expected similarity ≈ 0.90, got {similarity}"
                )

                # The orthogonal encoding.py should NOT appear (similarity ≈ 0.0 < threshold 0.3)
                assert "src/encoding.py" not in file_paths, (
                    "encoding.py should be filtered by threshold (similarity ≈ 0.0)"
                )

                # Verify embedding service was called (the actual production code path)
                mock_emb_svc.generate_embedding.assert_called_once_with(
                    "How does signing work?"
                )

            finally:
                # Cleanup: remove test data
                await db.execute(delete(Repository).where(Repository.id == test_repo_id))
                await db.commit()

    @pytest.mark.asyncio
    async def test_chat_service_retrieve_unanswerable_returns_empty(self):
        """Production path with a query orthogonal to all stored embeddings.

        Verifies that when no embedding exceeds the similarity threshold,
        the real vector_search returns [] and ChatService propagates it cleanly.
        """
        try:
            user_id = await _probe_live_db()
            if not user_id:
                pytest.skip("No user in database for test repository FK")
        except Exception as e:
            pytest.skip(f"Live PostgreSQL database not reachable: {e}")

        test_repo_id = uuid4()

        async with AsyncSessionLocal() as db:
            repo = Repository(
                id=test_repo_id,
                user_id=user_id,
                full_name=f"__test__/chat_unanswerable_{test_repo_id.hex[:8]}",
                repo_name="chat_unanswerable",
                url="https://github.com/test/chat_unanswerable",
                indexing_status="complete",
                indexing_mode="full",
            )
            db.add(repo)
            await db.flush()

            try:
                embedding_repo = EmbeddingRepository(db)

                # Single embedding in dimension 0
                v_stored = [1.0] + [0.0] * 1535
                await embedding_repo.create_bulk([
                    {
                        "id": uuid4(),
                        "repo_id": test_repo_id,
                        "file_path": "src/signer.py",
                        "chunk_index": 0,
                        "chunk_text": "class Signer: signs data",
                        "embedding": v_stored,
                    },
                ])
                await db.commit()

                # Query vector orthogonal to all stored embeddings
                # cos_sim ≈ 0.0, well below threshold 0.3
                query_vec = [0.0, 0.0, 1.0] + [0.0] * 1533

                with patch("app.services.chat.EmbeddingService") as MockEmbSvc:
                    mock_emb_svc = MockEmbSvc.return_value
                    mock_emb_svc.generate_embedding = AsyncMock(return_value=query_vec)

                    chat_service = ChatService()
                    chat_service.embedding_service = mock_emb_svc

                    with patch("app.ai.context.pipeline.cache") as mock_cache:
                        mock_cache.get = AsyncMock(return_value=None)
                        mock_cache.set = AsyncMock()

                        results = await chat_service.retrieve_relevant_chunks(
                            repo_id=test_repo_id,
                            question="What is the weather today?",
                            embedding_repo=embedding_repo,
                            top_k=5,
                            expand_context=False,
                        )

                assert results == [], (
                    f"Expected empty results for orthogonal query, got {len(results)} results"
                )

            finally:
                await db.execute(delete(Repository).where(Repository.id == test_repo_id))
                await db.commit()
