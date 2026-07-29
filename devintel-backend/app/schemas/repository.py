from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RepositoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    github_repo_id: Optional[str] = None
    full_name: str
    repo_name: str
    description: Optional[str] = None
    url: Optional[str] = None
    stars: int = 0
    language: Optional[str] = None
    default_branch: str
    is_private: bool
    indexing_status: str
    last_indexed_commit: Optional[str] = None


class RepositoryCreate(BaseModel):
    repo_name: str
    full_name: str
    description: Optional[str] = None
    url: str
    stars: int = 0
    language: Optional[str] = None
    default_branch: str = "main"


class RepositoryCreateResponse(RepositoryPublic):
    pass


class RepositoryResponse(RepositoryPublic):
    pass


class RepositoryIndexRequest(BaseModel):
    repository_id: UUID


class RepositoryIndexResponse(BaseModel):
    task_id: str
    message: str
    repository_id: UUID


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryResponse]
    total: int


class IndexingStatusResponse(BaseModel):
    id: UUID
    indexed_status: str
    indexing_progress: int
    indexing_error: Optional[str]
    last_indexed_at: Optional[str]
    last_indexed_commit_sha: Optional[str]
    indexing_mode: Optional[str]


class SearchResult(BaseModel):
    file_path: str
    chunk_text: str
    similarity: float
    chunk_index: int


class SearchResponse(BaseModel):
    results: list[SearchResult]
    repository_id: UUID
    query: str


class RepositoryStatusResponse(IndexingStatusResponse):
    pass
