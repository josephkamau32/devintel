"""Embedding repository."""

from typing import List, Tuple
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import Embedding
from app.repositories.base import BaseRepository


class EmbeddingRepository(BaseRepository[Embedding]):
    """Embedding repository with vector similarity search."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        super().__init__(Embedding, db)

    async def create_bulk(self, embeddings_data: List[dict]) -> List[Embedding]:
        """Create multiple embeddings at once."""
        instances = [Embedding(**data) for data in embeddings_data]
        self.db.add_all(instances)
        await self.db.flush()
        for instance in instances:
            await self.db.refresh(instance)
        return instances

    async def get_by_id(self, embedding_id: UUID) -> Embedding | None:
        """Get embedding by ID."""
        result = await self.db.execute(
            select(Embedding).where(Embedding.id == embedding_id)
        )
        return result.scalars().first()

    async def vector_search(
        self,
        repo_id: UUID,
        query_embedding: List[float],
        top_k: int = 6,
        threshold: float = 0.3,
    ) -> List[Tuple[Embedding, float]]:
        """
        Perform vector similarity search using cosine distance.
        Returns list of (Embedding, similarity_score) tuples.
        """
        from app.core.constants import SIMILARITY_THRESHOLD
        
        # Use provided threshold or default from constants
        active_threshold = threshold if threshold is not None else SIMILARITY_THRESHOLD

        # Use pgvector's cosine distance operator
        query = text("""
            SELECT 
                id,
                repo_id,
                file_path,
                chunk_index,
                chunk_text,
                embedding,
                created_at,
                updated_at,
                (1 - (embedding <=> :query_embedding)) as similarity
            FROM embeddings
            WHERE repo_id = :repo_id 
              AND (1 - (embedding <=> :query_embedding)) >= :threshold
            ORDER BY embedding <=> :query_embedding
            LIMIT :top_k
        """)

        result = await self.db.execute(
            query,
            {
                "query_embedding": query_embedding,
                "repo_id": str(repo_id),
                "top_k": top_k,
                "threshold": active_threshold,
            },
        )

        rows = result.fetchall()
        embeddings_with_scores = []

        for row in rows:
            embedding = Embedding(
                id=row.id,
                repo_id=row.repo_id,
                file_path=row.file_path,
                chunk_index=row.chunk_index,
                chunk_text=row.chunk_text,
                embedding=row.embedding,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            similarity = row.similarity
            embeddings_with_scores.append((embedding, similarity))

        return embeddings_with_scores

    async def delete_by_repo(self, repo_id: UUID) -> int:
        """Delete all embeddings for a repository."""
        from sqlalchemy import delete

        result = await self.db.execute(
            delete(Embedding).where(Embedding.repo_id == repo_id)
        )
        await self.db.flush()
        return result.rowcount

    async def get_neighbors(self, repo_id: UUID, file_path: str, chunk_index: int, radius: int = 1) -> List[Embedding]:
        """Fetch adjacent chunks for a given file and chunk index."""
        result = await self.db.execute(
            select(Embedding)
            .where(
                Embedding.repo_id == repo_id,
                Embedding.file_path == file_path,
                Embedding.chunk_index >= chunk_index - radius,
                Embedding.chunk_index <= chunk_index + radius
            )
            .order_by(Embedding.chunk_index.asc())
        )
        return list(result.scalars().all())
