"""Chat service for RAG."""

import hashlib
from typing import AsyncGenerator, List, Tuple
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient
from app.models.embedding import Embedding
from app.repositories.embedding import EmbeddingRepository
from app.services.cache import cache
from app.services.embedding import EmbeddingService

logger = get_logger(__name__)


class ChatService:
    """Service for RAG-powered chat."""

    def __init__(self):
        """Initialize service."""
        self.openai_client = OpenAIClient()
        self.embedding_service = EmbeddingService()

    @staticmethod
    def build_system_prompt(repo_name: str, context_chunks: List[Tuple[Embedding, float]]) -> str:
        """Build system prompt with retrieved context."""
        context_text = ""
        
        for embedding, similarity in context_chunks:
            context_text += f"\n\n--- File: {embedding.file_path} (Chunk {embedding.chunk_index}, Similarity: {similarity:.3f}) ---\n"
            context_text += embedding.chunk_text
        
        system_prompt = f"""You are an expert code assistant for the repository: {repo_name}

Context from codebase:
{context_text}

Rules:
- ONLY use the provided context to answer questions
- If the answer is not in the context, say "I don't have enough information in the provided context"
- Be specific and cite file paths when possible
- Do not make assumptions beyond the provided code
- Focus on helping developers understand their codebase
"""
        return system_prompt

    async def retrieve_relevant_chunks(
        self,
        repo_id: UUID,
        question: str,
        embedding_repo: EmbeddingRepository,
        top_k: int = settings.top_k_chunks,
    ) -> List[Tuple[Embedding, float]]:
        """Retrieve relevant chunks using vector similarity search."""
        # Check cache
        cache_key = f"embed:{repo_id}:{hashlib.md5(question.encode()).hexdigest()}"
        cached_result = await cache.get(cache_key)
        
        if cached_result:
            logger.info("Retrieved chunks from cache")
            # Note: This is simplified - in production, reconstruct Embedding objects
            return []
        
        # Generate question embedding
        question_embedding = await self.embedding_service.generate_embedding(question)
        
        # Vector search
        results = await embedding_repo.vector_search(
            repo_id=repo_id,
            query_embedding=question_embedding,
            top_k=top_k,
        )
        
        # Cache results
        await cache.set(cache_key, results, ttl=3600)
        
        return results

    async def stream_chat(
        self,
        repo_name: str,
        question: str,
        context_chunks: List[Tuple[Embedding, float]],
    ) -> AsyncGenerator[str, None]:
        """Stream chat response."""
        system_prompt = self.build_system_prompt(repo_name, context_chunks)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        
        async for chunk in self.openai_client.chat_completion_stream(messages):
            yield chunk
