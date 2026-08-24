from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RepositoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID

    full_name: str
    repo_name: str
    description: Optional[str] = None
    url: Optional[str] = None
    stars: int = 0
    language: Optional[str] = None
    default_branch: str

    indexing_status: str



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
    indexing_status: str
    indexing_progress: int
    indexing_error: Optional[str] = None
    last_indexed_at: Optional[str] = None
    last_indexed_commit_sha: Optional[str] = None
    indexing_mode: Optional[str] = None


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
