"""Architect Agent for large-scale code refactoring."""

from typing import Any, Optional

from app.core.logging import get_logger
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.agents.base_agent import AgentResponse, BaseAgent

logger = get_logger(__name__)


class ArchitectAgent(BaseAgent):
    """Agent specialized in architecture, refactoring, and design patterns."""

    AGENT_TYPE = "architect"

    ARCHITECTURE_KEYWORDS = [
        "refactor", "restructure", "redesign", "migrate", "architecture",
        "module", "package", "layer", "pattern", "coupling", "cohesion",
        "dependency", "boundaries", "clean architecture", "hexagonal",
    ]

    def __init__(self):
        super().__init__()

    def get_toolset(self) -> list[dict]:
        """Return architecture-focused tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_architecture",
                    "description": "Analyze the repository's architectural patterns and suggest improvements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "focus_area": {
                                "type": "string",
                                "description": "Specific area to analyze (e.g., 'module boundaries', 'dependency structure', 'layer violations')",
                            },
                        },
                        "required": ["focus_area"],
                    },
                },
            },
        ]

    def build_system_prompt(
        self,
        repo_name: str,
        context_chunks: list[tuple[Any, float]],
    ) -> str:
        """Build architecture-focused system prompt."""
        context_text = ""
        for embedding, similarity in context_chunks:
            context_text += f"\n\n--- File: {embedding.file_path} ---\n{embedding.chunk_text}\n"

        if not context_chunks:
            context_text = "\n[No relevant code was found for this query.]\n"

        return f"""You are DevIntel Architect, an elite software architect analyzing repository: {repo_name}

Context from codebase:
{context_text}

Your expertise:
- Module boundaries and cohesion
- Dependency inversion and injection patterns
- Clean architecture / hexagonal architecture principles
- Code organization and package structure
- Design pattern identification and refactoring

Provide actionable architectural recommendations. Cite specific files and suggest concrete changes."""

    async def run(
        self,
        query: str,
        repo: Repository,
        embedding_repo: EmbeddingRepository,
        chat_history: Optional[list[dict]] = None,
    ) -> AgentResponse:
        """Run architect analysis."""
        from app.services.retrieval.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever(embedding_repo)
        results = await retriever.search(repo.id, query, top_k=8)

        context_chunks = [(r.embedding, r.score) for r, _ in results]

        system_prompt = self.build_system_prompt(repo.full_name, context_chunks)

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            for msg in chat_history:
                messages.append(msg)

        messages.append({"role": "user", "content": query})

        response = await self.openai_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.content if hasattr(response, "content") else str(response)

        return AgentResponse(
            agent_type=self.AGENT_TYPE,
            content=content,
            confidence=self._classify_intent(query),
        )

    def _classify_intent(self, query: str) -> float:
        """Return confidence that this is an architecture query."""
        query_lower = query.lower()
        matches = sum(1 for kw in self.ARCHITECTURE_KEYWORDS if kw in query_lower)
        return min(1.0, matches / 2.0)
