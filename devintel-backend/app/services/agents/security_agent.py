"""Security Auditor Agent for vulnerability analysis."""

from typing import Any, Optional

from app.core.logging import get_logger
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.agents.base_agent import AgentResponse, BaseAgent

logger = get_logger(__name__)


class SecurityAuditorAgent(BaseAgent):
    """Agent specialized in security analysis."""

    AGENT_TYPE = "security"

    SECURITY_KEYWORDS = [
        "security", "vulnerability", "auth", "injection", "owasp", "sqli", "xss",
        "csrf", "secrets", "password", "token", "jwt", "encryption", "hash",
        "sanitize", "validate", "authenticate", "authorize", "permission",
    ]

    def __init__(self):
        super().__init__()

    def get_toolset(self) -> list[dict]:
        """Return security-focused tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "scan_for_secrets",
                    "description": "Scan code for exposed secrets, API keys, and credentials",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_owasp_top10",
                    "description": "Analyze code for OWASP Top 10 vulnerabilities",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

    def build_system_prompt(
        self,
        repo_name: str,
        context_chunks: list[tuple[Any, float]],
    ) -> str:
        return f"""You are DevIntel Security Auditor. Analyze repository: {repo_name}

Focus on:
- OWASP Top 10 vulnerabilities
- Secret/key exposure
- Authentication/authorization flaws
- SQL injection, XSS, CSRF risks

Context from codebase:
{self._build_context(context_chunks)}

Report security findings with severity and mitigation suggestions."""

    def _build_context(self, chunks: list[tuple[Any, float]]) -> str:
        return "".join(
            f"\n--- {emb.file_path} ---\n{emb.chunk_text[:800]}"
            for emb, _ in chunks
        ) if chunks else "\n[No relevant code found]"

    async def run(
        self,
        query: str,
        repo: Repository,
        embedding_repo: EmbeddingRepository,
        chat_history: Optional[list[dict]] = None,
    ) -> AgentResponse:
        from app.services.retrieval.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever(embedding_repo)
        results = await retriever.search(repo.id, query, top_k=10)
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
        matches = sum(1 for kw in self.SECURITY_KEYWORDS if kw in query_lower)
        return min(1.0, matches / 2.0)
