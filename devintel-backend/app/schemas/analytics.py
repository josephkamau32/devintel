"""Analytics schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    """Analytics response schema."""

    id: UUID
    user_id: UUID
    query_count: int
    token_usage: int
    repositories_indexed: int
    last_active_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class UsageTrend(BaseModel):
    """Daily query usage trend."""
    date: str
    queries: int


class RepoUsage(BaseModel):
    """Query usage per repository."""
    repo_name: str
    queries: int


class AnalyticsDashboard(BaseModel):
    """Aggregate analytics for the user dashboard."""
    total_queries: int
    total_tokens: int
    total_repos_indexed: int
    usage_trend: List[UsageTrend]
    top_repositories: List[RepoUsage]
    last_active_at: datetime | None
