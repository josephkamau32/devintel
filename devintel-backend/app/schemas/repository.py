"""Repository schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class RepositoryBase(BaseModel):
    """Base repository schema."""

    repo_name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = None
    url: str = Field(..., description="Repository URL")
    stars: int = Field(default=0, description="Number of stars")
    language: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    """Repository creation schema."""

    pass


class RepositoryResponse(RepositoryBase):
    """Repository response schema."""

    id: UUID
    user_id: UUID
    indexed_status: bool
    last_indexed_at: Optional[datetime] = None
    indexing_error: Optional[str] = None
    indexing_progress: int = Field(default=0, ge=0, le=100)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class RepositoryListResponse(BaseModel):
    """Repository list response schema."""

    repositories: List[RepositoryResponse]
    total: int


class RepositoryIndexRequest(BaseModel):
    """Repository indexing request schema."""

    repository_id: UUID = Field(..., description="Repository ID to index")


class RepositoryIndexResponse(BaseModel):
    """Repository indexing response schema."""

    task_id: str = Field(..., description="Celery task ID")
    message: str
    repository_id: UUID
