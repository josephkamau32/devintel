"""Test Engineer Agent for test generation and coverage analysis."""

from typing import Any, Optional

from app.core.logging import get_logger
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.agents.base_agent import AgentResponse, BaseAgent

logger = get_logger(__name__)


class TestEngineerAgent(BaseAgent):
    """Agent specialized in testing and coverage."""

    AGENT_TYPE = "test_engineer"

    TEST_KEYWORDS = [
        "test", "coverage", "unit", "integration", "mock", "assert", "fixture",
        "pytest", "jest", "vitest", "cypress", "e2e", "tdd", "testing",
        "coverage", "coverage gap", "uncovered", "missing test",
    ]

    def __init__(self):
        super().__init__()

    def get_toolset(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_tests",
                    "description": "Generate unit/integration tests for code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "test_type": {"type": "string", "enum": ["unit", "integration", "e2e"]},
                        },
                    },
                },
            },
        ]

    def build_system_prompt(
        self,
        repo_name: str,
        context_chunks: list[tuple[Any, float]],
    ) -> str:
        context_text = "".join(
            f"\n--- {emb.file_path} ---\n{emb.chunk_text[:1200]}"
            for emb, _ in context_chunks
        ) if context_chunks else "\n[No relevant code found]"

        return f"""You are DevIntel Test Engineer. Analyze repository: {repo_name}

Focus on:
- Test coverage gaps
- Unit test generation
- Integration test strategies
- Mocking patterns
- Assertion quality

{context_text}

Generate comprehensive test suggestions and identify uncovered code paths."""

    async def run(
        self,
        query: str,
        repo: Repository,
        embedding_repo: EmbeddingRepository,
        chat_history: Optional[list[dict]] = None,
    ) -> AgentResponse:
        from app.services.retrieval.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever(embedding_repo)
        results = await retriever.search(repo.id, query, top_k=8)
        context_chunks = [(r.embedding, r.score) for r, _ in results]

        system_prompt = self.build_system_prompt(repo.full_name, context_chunks)
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": query})

        response = await self.openai_client.chat_completion(
            messages=messages, temperature=0.2, max_tokens=2000
        )

        return AgentResponse(
            agent_type=self.AGENT_TYPE,
            content=response.content if hasattr(response, "content") else str(response),
            confidence=self._classify_intent(query),
        )

    def _classify_intent(self, query: str) -> float:
        query_lower = query.lower()
        matches = sum(1 for kw in self.TEST_KEYWORDS if kw in query_lower)
        return min(1.0, matches / 2.0)
