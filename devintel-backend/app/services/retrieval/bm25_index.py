"""BM25 index for keyword-based retrieval.

Uses rank_bm25 for TF-IDF style search over code chunks.
"""

import asyncio
from typing import Optional
from uuid import UUID

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None  # type: ignore

from app.core.logging import get_logger
from app.repositories.embedding import EmbeddingRepository

logger = get_logger(__name__)


class ScoredChunk:
    """Container for a scored chunk."""

    def __init__(self, embedding, score: float, source: str = "bm25"):
        self.embedding = embedding
        self.score = score
        self.source = source

    def __repr__(self):
        return f"ScoredChunk(file={self.embedding.file_path}, score={self.score:.4f}, source={self.source})"


class BM25Index:
    """
    BM25 index per repository for keyword-based search.

    Uses LRU cache to manage memory within the 512MB constraint.
    """

    def __init__(self, embedding_repo: EmbeddingRepository):
        self.embedding_repo = embedding_repo
        self._indices: dict[str, tuple[BM25Okapi, list]] = {}  # repo_id -> (bm25, chunks)
        self._lock = asyncio.Lock()

    async def search(
        self,
        repo_id: UUID,
        query: str,
        top_k: int = 10,
    ) -> list[ScoredChunk]:
        """
        Search the BM25 index for a repository.

        Args:
            repo_id: Repository UUID
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of ScoredChunk objects sorted by BM25 score
        """
        if BM25Okapi is None:
            logger.warning("rank_bm25 not installed, BM25 search disabled")
            return []

        async with self._lock:
            # Get or build index
            bm25, chunks = await self._get_or_build_index(repo_id)
            if not bm25 or not chunks:
                return []

            # Tokenize query
            tokenized_query = self._tokenize(query)

            # Get scores
            scores = bm25.get_scores(tokenized_query)

            # Get top-k indices
            import numpy as np
            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    results.append(ScoredChunk(chunks[idx], float(scores[idx]), "bm25"))

            return results

    async def _get_or_build_index(self, repo_id: UUID) -> tuple[Optional[BM25Okapi], list]:
        """Get cached index or build it from database."""
        cache_key = str(repo_id)

        if cache_key in self._indices:
            return self._indices[cache_key]

        # Build index from all chunks in repository
        all_embeddings = await self.embedding_repo.get_all_by_repo(repo_id)

        if not all_embeddings:
            self._indices[cache_key] = (None, [])
            return (None, [])

        chunks = list(all_embeddings)
        tokenized_corpus = [self._tokenize(emb.chunk_text) for emb in chunks]

        # Build BM25 index
        bm25 = BM25Okapi(tokenized_corpus)
        self._indices[cache_key] = (bm25, chunks)

        logger.info(f"Built BM25 index for repo {repo_id} with {len(chunks)} chunks")
        return (bm25, chunks)

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on non-alphanumeric
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    async def invalidate(self, repo_id: UUID) -> None:
        """Invalidate the BM25 cache for a repository."""
        cache_key = str(repo_id)
        if cache_key in self._indices:
            del self._indices[cache_key]
            logger.info(f"Invalidated BM25 cache for repo {repo_id}")

    async def clear(self) -> None:
        """Clear all cached indices."""
        self._indices.clear()
        logger.info("Cleared all BM25 caches")