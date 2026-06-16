"""Repository schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RepositoryBase(BaseModel):
    """Base repository schema."""

    repo_name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = None
    url: str = Field(..., description="Repository URL")
    stars: int = Field(default=0, description="Number of stars")
    language: Optional[str] = None
    default_branch: str = Field(default="main", description="Default branch name (e.g. main, master)")


class RepositoryCreate(RepositoryBase):
    """Repository creation schema."""
    org_id: Optional[UUID] = Field(None, description="Optional Organization ID")


class SearchResult(BaseModel):
    """Semantic search result."""

    file_path: str
    chunk_text: str
    similarity: float
    chunk_index: int


class SearchResponse(BaseModel):
    """Search response schema."""

    results: list[SearchResult]
    repository_id: UUID
    query: str


class RepositoryResponse(RepositoryBase):
    """Repository response schema."""

    id: UUID
    user_id: Optional[UUID] = None
    org_id: Optional[UUID] = None
    indexed_status: bool
    last_indexed_at: Optional[datetime] = None
    indexing_error: Optional[str] = None
    indexing_progress: int = Field(default=0, ge=0, le=100)
    last_indexed_commit_sha: Optional[str] = None
    indexing_mode: str = Field(default="full", description="Indexing mode: 'full' or 'incremental'")
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class RepositoryListResponse(BaseModel):
    """Repository list response schema."""

    repositories: list[RepositoryResponse]
    total: int


class RepositoryIndexRequest(BaseModel):
    """Repository indexing request schema."""

    repository_id: UUID = Field(..., description="Repository ID to index")


class RepositoryIndexResponse(BaseModel):
    """Repository indexing response schema."""

    task_id: str = Field(..., description="Background task ID")
    message: str
    repository_id: UUID


class RepositoryStatusResponse(BaseModel):
    """Lightweight repository status for polling."""

    id: UUID
    indexed_status: bool
    indexing_progress: int = Field(default=0, ge=0, le=100)
    indexing_error: Optional[str] = None
    last_indexed_commit_sha: Optional[str] = None
    indexing_mode: str = Field(default="full", description="Indexing mode: 'full' or 'incremental'")


class IndexingStatusResponse(BaseModel):
    """Extended indexing status response."""

    id: UUID
    indexed_status: bool
    indexing_progress: int = Field(default=0, ge=0, le=100)
    indexing_error: Optional[str] = None
    last_indexed_at: Optional[datetime] = None
    last_indexed_commit_sha: Optional[str] = None
    indexing_mode: str = Field(default="full", description="Indexing mode: 'full' or 'incremental'")
