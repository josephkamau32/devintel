"""Base agent class for specialized AI agents."""

from typing import Any, Optional

from pydantic import BaseModel

from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository

logger = get_logger(__name__)


class AgentResponse(BaseModel):
    """Response from an agent."""

    agent_type: str
    content: str
    tool_calls: Optional[list[dict]] = None
    confidence: Optional[float] = None


class BaseAgent:
    """Abstract base class for specialized agents."""

    AGENT_TYPE = "base"

    def __init__(self):
        self.openai_client = OpenAIClient()

    def get_toolset(self) -> list[dict]:
        """Return the tool definitions available to this agent."""
        return []

    def build_system_prompt(
        self,
        repo_name: str,
        context_chunks: list[tuple[Any, float]],
    ) -> str:
        """Build a system prompt with retrieved context."""
        context_text = ""
        for embedding, similarity in context_chunks:
            context_text += f"\n\n--- File: {embedding.file_path} (Chunk {embedding.chunk_index}) ---\n"
            context_text += embedding.chunk_text

        if not context_chunks:
            context_text = "\n[No relevant code was found for this query.]\n"

        return f"""You are an AI assistant for the repository: {repo_name}

Context from codebase:
{context_text}

Rules:
- ONLY use the provided context to answer questions
- If the answer is not in the context, clearly say "I don't have enough information in the provided context to answer this question"
- Be specific and cite file paths when possible
- Do not make assumptions beyond the provided code
- Focus on helping developers understand their codebase"""

    async def run(
        self,
        query: str,
        repo: Repository,
        embedding_repo: EmbeddingRepository,
        chat_history: Optional[list[dict]] = None,
    ) -> AgentResponse:
        """Execute the agent on a query. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")

    def _classify_intent(self, query: str) -> float:
        """Return confidence score that this agent should handle the query."""
        return 0.0
