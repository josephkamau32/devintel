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
