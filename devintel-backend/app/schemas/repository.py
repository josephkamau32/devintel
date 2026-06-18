from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.models.repository import IndexingStatus


class RepositoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    github_repo_id: str
    full_name: str
    name: str
    description: Optional[str]
    default_branch: str
    is_private: bool
    indexing_status: IndexingStatus
    last_indexed_commit: Optional[str]


class RepositoryCreate(BaseModel):
    github_url: str


class RepositoryCreateResponse(RepositoryPublic):
    pass
