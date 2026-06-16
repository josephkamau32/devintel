"""Agent router for dispatching queries to specialized agents."""

from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.agents.architect_agent import ArchitectAgent
from app.services.agents.base_agent import AgentResponse, BaseAgent
from app.services.agents.performance_agent import PerformanceProfilerAgent
from app.services.agents.security_agent import SecurityAuditorAgent
from app.services.agents.security_remediation_agent import SecurityRemediationAgent
from app.services.agents.test_agent import TestEngineerAgent
from app.services.embedding import EmbeddingService

logger = get_logger(__name__)


class AgentRouter:
    """Routes queries to the appropriate specialized agent."""

    def __init__(self):
        self.agents = {
            "architect": ArchitectAgent(),
            "security": SecurityAuditorAgent(),
            "security_remediation": SecurityRemediationAgent(),
            "performance": PerformanceProfilerAgent(),
            "test_engineer": TestEngineerAgent(),
        }
        self.classifier = EmbeddingService()

    def get_agent(self, agent_type: Optional[str] = None, query: str = "") -> BaseAgent:
        """
        Get the appropriate agent by type or query classification.

        If agent_type is provided, returns that agent directly.
        Otherwise, classifies the query and returns the best matching agent.
        Falls back to the architect agent (most general) if no strong match.
        """
        if agent_type and agent_type in self.agents:
            return self.agents[agent_type]

        # Classify query by intent
        scores = {
            name: agent._classify_intent(query)
            for name, agent in self.agents.items()
        }

        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]

        # Threshold for fallback to generalist
        if best_score < 0.3:
            logger.info(f"Low agent confidence ({best_score}), using architect as generalist")
            return self.agents["architect"]

        logger.info(f"Routed query to {best_agent} agent (confidence: {best_score:.2f})")
        return self.agents[best_agent]

    async def route(
        self,
        query: str,
        repo: Repository,
        embedding_repo: EmbeddingRepository,
        chat_history: Optional[list[dict]] = None,
        agent_type: Optional[str] = None,
    ) -> AgentResponse:
        """Route query to agent and return response."""
        agent = self.get_agent(agent_type, query)
        return await agent.run(query, repo, embedding_repo, chat_history)