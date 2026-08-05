"""Context pipeline — unified retrieval → expansion → rerank → compress.

This replaces the inline retrieval + N+1 expansion logic that was
previously embedded in ChatService.retrieve_relevant_chunks().

The pipeline is composable: each stage is an independent object that
can be swapped, mocked, or extended without touching the others.

Usage::

    pipeline = ContextPipeline(embedding_service)
    chunks = await pipeline.retrieve(
        repo_id=repo_id,
        query="explain auth flow",
        embedding_repo=embedding_repo,
        top_k=5,
        expand=True,
    )
    context_str = pipeline.compressor.format_context(chunks)
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional
from uuid import UUID

from app.ai.context.compressor import ContextCompressor
from app.ai.context.reranker import ContextReranker
from app.core.logging import get_logger
from app.services.cache import cache

logger = get_logger(__name__)


class ContextPipeline:
    """End-to-end context retrieval pipeline.

    Stages:
    1. **Embed** the query
    2. **Vector search** for top-K matches
    3. **Expand** via neighbor chunks (single batched query)
    4. **Rerank** for precision
    5. **Compress** to fit within token budget
    """

    def __init__(
        self,
        embedding_service,
        *,
        compressor: Optional[ContextCompressor] = None,
        reranker: Optional[ContextReranker] = None,
    ) -> None:
        self.embedding_service = embedding_service
        self.compressor = compressor or ContextCompressor()
        self.reranker = reranker or ContextReranker()

    async def retrieve(
        self,
        repo_id: UUID,
        query: str,
        embedding_repo,
        *,
        top_k: int = 5,
        expand: bool = True,
        expand_radius: int = 1,
        cache_ttl: int = 3600,
    ) -> list[tuple[Any, float]]:
        """Run the full context pipeline.

        Args:
            repo_id: Repository to search.
            query: User query text.
            embedding_repo: EmbeddingRepository instance.
            top_k: Number of top chunks to retrieve.
            expand: Whether to include adjacent chunks.
            expand_radius: How many neighbors on each side.
            cache_ttl: Cache TTL in seconds (0 to disable).

        Returns:
            Compressed, ranked list of (Embedding, similarity) tuples.
        """
        # Stage 0: Check cache
        cache_key = f"ctx:{repo_id}:{hashlib.sha256(query.encode()).hexdigest()}"
        cached = await self._try_cache(cache_key, embedding_repo)
        if cached:
            return cached

        # Stage 1: Embed the query
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Stage 2: Vector search
        raw_results = await embedding_repo.vector_search(
            repo_id=repo_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )

        if not raw_results:
            return []

        # Stage 3: Expand via batched neighbor query (fixes N+1)
        if expand:
            raw_results = await self._expand_neighbors(
                repo_id=repo_id,
                results=raw_results,
                embedding_repo=embedding_repo,
                radius=expand_radius,
            )

        # Stage 4: Rerank
        ranked = await self.reranker.rerank(query, raw_results, top_k=top_k * 3)

        # Stage 5: Compress
        compressed = self.compressor.compress(ranked)

        # Cache the result
        if cache_ttl > 0:
            await self._write_cache(cache_key, compressed, ttl=cache_ttl)

        return compressed

    async def _expand_neighbors(
        self,
        repo_id: UUID,
        results: list[tuple[Any, float]],
        embedding_repo,
        radius: int = 1,
    ) -> list[tuple[Any, float]]:
        """Expand results with adjacent chunks using a single batched query.

        Replaces the old N+1 loop with one batch_get_neighbors() call.
        """
        # Build the batch request
        chunk_keys = [(emb.file_path, emb.chunk_index) for emb, _ in results]

        # Single database query for all neighbors
        all_neighbors = await embedding_repo.batch_get_neighbors(
            repo_id=repo_id,
            chunks=chunk_keys,
            radius=radius,
        )

        # Build a lookup of original scores
        score_map: dict[tuple[str, int], float] = {}
        for emb, score in results:
            score_map[(emb.file_path, emb.chunk_index)] = score

        # Assign scores: original hits keep their score, neighbors get 0.95× decay
        expanded: dict[tuple[str, int], tuple[Any, float]] = {}
        for neighbor in all_neighbors:
            key = (neighbor.file_path, neighbor.chunk_index)
            if key in score_map:
                # Original hit
                expanded[key] = (neighbor, score_map[key])
            elif key not in expanded:
                # Find the closest original hit for this file to inherit score from
                best_score = 0.0
                for (fp, ci), sc in score_map.items():
                    if fp == neighbor.file_path:
                        best_score = max(best_score, sc)
                expanded[key] = (neighbor, best_score * 0.95)

        # Return sorted by file_path then chunk_index
        sorted_keys = sorted(expanded.keys())
        return [expanded[k] for k in sorted_keys]

    async def _try_cache(
        self,
        cache_key: str,
        embedding_repo,
    ) -> list[tuple[Any, float]] | None:
        """Try to load results from cache."""
        cached_raw = await cache.get(cache_key)
        if not cached_raw:
            return None

        try:
            cached_data = json.loads(cached_raw)
            results = []
            for item in cached_data:
                emb = await embedding_repo.get_by_id(UUID(item["embedding_id"]))
                if emb:
                    results.append((emb, item["similarity"]))
            if results:
                logger.info("Context pipeline: cache hit (%d chunks)", len(results))
                return results
        except Exception as e:
            logger.warning("Context pipeline: cache deserialization failed: %s", e)

        return None

    async def _write_cache(
        self,
        cache_key: str,
        chunks: list[tuple[Any, float]],
        ttl: int,
    ) -> None:
        """Write results to cache."""
        try:
            cache_data = [
                {"embedding_id": str(emb.id), "similarity": score}
                for emb, score in chunks
            ]
            await cache.set(cache_key, json.dumps(cache_data), ttl=ttl)
        except Exception as e:
            logger.warning("Context pipeline: cache write failed: %s", e)
