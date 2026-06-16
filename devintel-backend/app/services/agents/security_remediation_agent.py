"""Security Remediation Agent for auto-fixing vulnerabilities."""

from typing import Any, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.agents.base_agent import AgentResponse, BaseAgent

logger = get_logger(__name__)


class SecurityRemediationAgent(BaseAgent):
    """Agent specialized in security remediation and auto-fixing."""

    AGENT_TYPE = "security_remediation"

    REMEDIATION_KEYWORDS = [
        "fix", "remediate", "patch", "secure", "sanitize", "escape",
        "validate", "authenticate", "authorize", "encrypt", "hash",
    ]

    def __init__(self):
        super().__init__()

    def get_toolset(self) -> list[dict]:
        """Return security remediation tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_security_fix",
                    "description": "Generate code fix for a security vulnerability",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "vulnerability": {"type": "string"},
                            "fix_type": {"type": "string", "enum": ["input_sanitization", "auth_fix", "secret_rotation"]},
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
        return f"""You are DevIntel Security Remediation Agent. Analyze and fix vulnerabilities in: {repo_name}

Focus on:
- Input validation and sanitization
- Authentication/authorization fixes
- Secret/credential remediation
- OWASP Top 10 mitigations

Context from codebase:
{self._build_context(context_chunks)}

Provide secure code fixes with explanations."""

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
            messages=messages, temperature=0.1, max_tokens=2500
        )

        return AgentResponse(
            agent_type=self.AGENT_TYPE,
            content=response.content if hasattr(response, "content") else str(response),
            confidence=self._classify_intent(query),
        )

    def _classify_intent(self, query: str) -> float:
        query_lower = query.lower()
        matches = sum(1 for kw in self.REMEDIATION_KEYWORDS if kw in query_lower)
        return min(1.0, matches / 1.5)