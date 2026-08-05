"""Hybrid retriever combining vector, BM25, and call-graph search."""

import asyncio
from enum import Enum
from typing import Optional
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger
from app.repositories.embedding import EmbeddingRepository
from app.services.embedding import EmbeddingService
from app.services.retrieval.bm25_index import BM25Index, ScoredChunk
from app.services.retrieval.rrf import reciprocal_rank_fusion

logger = get_logger(__name__)


class RetrievalMode(str, Enum):
    """Retrieval mode options."""

    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"


class HybridRetriever:
    """
    Combines vector similarity, BM25 keyword search, and call-graph expansion.

    Uses Reciprocal Rank Fusion to merge results.
    """

    def __init__(self, embedding_repo: EmbeddingRepository):
        self.embedding_service = EmbeddingService()
        self.bm25_index = BM25Index(embedding_repo)
        self.embedding_repo = embedding_repo

    async def search(
        self,
        repo_id: UUID,
        query: str,
        top_k: int = 10,
        mode: Optional[RetrievalMode] = None,
    ) -> list[tuple[ScoredChunk, float]]:
        """
        Perform hybrid search across multiple retrieval methods.

        Args:
            repo_id: Repository UUID
            query: Search query
            top_k: Number of results to return
            mode: Retrieval mode (defaults to config)

        Returns:
            List of (ScoredChunk, original_score) tuples
        """
        mode = mode or RetrievalMode(settings.RETRIEVAL_MODE if hasattr(settings, 'retrieval_mode') else RetrievalMode.VECTOR)

        # Get results from each method in parallel
        vector_results = []
        bm25_results = []

        if mode == RetrievalMode.VECTOR or mode == RetrievalMode.HYBRID:
            vector_results = await self._vector_search(repo_id, query, top_k)

        if mode == RetrievalMode.BM25 or mode == RetrievalMode.HYBRID:
            bm25_results = await self.bm25_index.search(repo_id, query, top_k)

        if mode == RetrievalMode.HYBRID:
            return await self._fuse_and_expand(repo_id, vector_results, bm25_results, top_k)

        return vector_results

    async def _vector_search(
        self,
        repo_id: UUID,
        query: str,
        top_k: int,
    ) -> list[tuple[ScoredChunk, float]]:
        """Perform vector similarity search."""
        query_embedding = await self.embedding_service.generate_embedding(query)

        results = await self.embedding_repo.vector_search(
            repo_id=repo_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )

        return [
            (ScoredChunk(emb, sim, "vector"), sim)
            for emb, sim in results
        ]

    async def _fuse_and_expand(
        self,
        repo_id: UUID,
        vector_results: list[tuple[ScoredChunk, float]],
        bm25_results: list[ScoredChunk],
        top_k: int,
    ) -> list[tuple[ScoredChunk, float]]:
        """
        Fuse vector and BM25 results, then expand via call graph.
        """
        # Prepare ranked lists for RRF (convert tuple to ScoredChunk list)
        vector_chunks = [sc for sc, _ in vector_results]
        bm25_chunks = [sc for sc in bm25_results]

        # Fuse using RRF
        fused = reciprocal_rank_fusion([vector_chunks, bm25_chunks])

        if not fused:
            return []

        # Expand via call graph (get callers/callees of top results)
        expanded = await self._expand_via_call_graph(repo_id, fused[:top_k])

        # Merge and deduplicate
        seen_ids = set()
        final_results = []

        for scored_chunk in expanded:
            emb_id = str(scored_chunk.embedding.id)
            if emb_id not in seen_ids:
                seen_ids.add(emb_id)
                final_results.append((scored_chunk, scored_chunk.score))

        return final_results[:top_k * 2]  # Return more to account for expansion

    async def _expand_via_call_graph(
        self,
        repo_id: UUID,
        chunks: list[ScoredChunk],
    ) -> list[ScoredChunk]:
        """
        Expand results by traversing call graph edges.
        """
        expanded = list(chunks)

        for scored_chunk in chunks:
            # Get neighboring chunks (callers and callees)
            neighbors = await self.embedding_repo.get_neighbors(
                repo_id=repo_id,
                file_path=scored_chunk.embedding.file_path,
                chunk_index=scored_chunk.embedding.chunk_index,
                radius=2,  # Get context around the chunk
            )

            for neighbor in neighbors:
                if neighbor.id not in [c.embedding.id for c in expanded]:
                    # Decay score for neighbors
                    expanded.append(ScoredChunk(neighbor, scored_chunk.score * 0.8, "graph"))

        return expanded

    async def invalidate_cache(self, repo_id: UUID) -> None:
        """Invalidate BM25 cache after reindexing."""
        await self.bm25_index.invalidate(repo_id)

    async def search_cross_repo(
        self,
        query: str,
        repo_ids: list[UUID],
        top_k: int = 20,
    ) -> list[tuple[ScoredChunk, float]]:
        """
        Search across multiple repositories for cross-repo knowledge.

        Args:
            query: Search query
            repo_ids: List of repository IDs to search (excludes source repo)
            top_k: Number of results to return

        Returns:
            List of similar chunks with scores
        """
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Get results from all repos combined
        all_results = []
        for repo_id in repo_ids:
            results = await self.embedding_repo.vector_search(
                repo_id=repo_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
            for emb, sim in results:
                all_results.append((ScoredChunk(emb, sim, "cross_repo"), sim))

        # Sort by score
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:top_k]
