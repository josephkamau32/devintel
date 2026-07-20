"""Cross-repository knowledge service."""

from typing import Any

from app.core.logging import get_logger
from app.models.repository import Repository
from app.services.retrieval.hybrid_retriever import HybridRetriever

logger = get_logger(__name__)


class CrossRepoKnowledgeService:
    """Service for discovering patterns across repositories."""

    def __init__(self, db_session):
        self.db = db_session
        self.hybrid_retriever = HybridRetriever()

    async def find_similar_patterns(
        self,
        repository: Repository,
        pattern_type: str,
        query: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find similar code patterns across all user repositories.

        Args:
            repository: Source repository
            pattern_type: Type of pattern (architecture, security, testing)
            query: Search query for the pattern
            top_k: Number of similar patterns to find

        Returns:
            List of similar patterns with similarity scores
        """
        # Retrieve similar code across repositories
        results = await self.hybrid_retriever.search_cross_repo(
            query=query,
            repo_ids=[repository.id],
            top_k=top_k * 2,  # Fetch more to filter
        )

        # Filter out same-repo results
        cross_repo_results = []
        for embedding, score in results:
            if embedding.repo_id != repository.id:
                cross_repo_results.append({
                    "repo_id": str(embedding.repo_id),
                    "file_path": embedding.file_path,
                    "chunk_text": embedding.chunk_text[:500],
                    "similarity_score": score,
                    "pattern_type": pattern_type,
                })

        return cross_repo_results[:top_k]

    async def build_knowledge_base(
        self,
        repository: Repository,
    ) -> dict:
        """Build cross-repo knowledge base for a repository."""
        # This would analyze patterns and store them for future similarity search
        # For now, return a placeholder
        return {
            "patterns_found": 0,
            "message": "Cross-repo knowledge base building is async",
        }
