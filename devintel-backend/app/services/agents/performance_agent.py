"""Performance Profiler Agent for optimization analysis."""

from typing import Any, Optional

from app.core.logging import get_logger
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.agents.base_agent import AgentResponse, BaseAgent

logger = get_logger(__name__)


class PerformanceProfilerAgent(BaseAgent):
    """Agent specialized in performance analysis."""

    AGENT_TYPE = "performance"

    PERFORMANCE_KEYWORDS = [
        "slow", "optimize", "bottleneck", "performance", "n+1", "query",
        "database", "index", "cache", "memory", "cpu", "latency", "throughput",
        "profiling", "benchmark", "efficiency", "complexity", "big o",
    ]

    def __init__(self):
        super().__init__()

    def get_toolset(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_query_complexity",
                    "description": "Analyze algorithmic complexity and database query efficiency",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_n_plus_one",
                    "description": "Detect N+1 query patterns in database code",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

    def build_system_prompt(
        self,
        repo_name: str,
        context_chunks: list[tuple[Any, float]],
    ) -> str:
        context_text = "".join(
            f"\n--- {emb.file_path} ---\n{emb.chunk_text[:1000]}"
            for emb, _ in context_chunks
        ) if context_chunks else "\n[No relevant code found]"

        return f"""You are DevIntel Performance Profiler. Analyze repository: {repo_name}

Focus on:
- Algorithmic complexity (Big O)
- Database query efficiency
- N+1 query patterns
- Cache opportunities
- Memory/CPU usage

{context_text}

Identify specific performance bottlenecks and suggest optimizations."""

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

        response = await self.orchestrator.complete(
            messages=messages, temperature=0.2, max_tokens=2000, agent="performance"
        )

        return AgentResponse(
            agent_type=self.AGENT_TYPE,
            content=response.content,
            confidence=self._classify_intent(query),
        )

    def _classify_intent(self, query: str) -> float:
        query_lower = query.lower()
        matches = sum(1 for kw in self.PERFORMANCE_KEYWORDS if kw in query_lower)
        return min(1.0, matches / 2.0)
