"""Git history schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class GitHistoryResponse(BaseModel):
    """Git history entry response."""

    sha: str
    message: str
    author_name: str
    author_email: str
    committed_at: Optional[datetime]
    files_changed: int
    additions: int
    deletions: int
    changed_files: Optional[list[str]] = None

    class Config:
        from_attributes = True


class FileBlameResponse(BaseModel):
    """File blame response."""

    file_path: str
    line_number: int
    line_content: str
    commit_sha: str
    commit_message: Optional[str]
    author_name: Optional[str]
    commit_date: Optional[datetime]

    class Config:
        from_attributes = True


class BlameRequest(BaseModel):
    """Request to get blame for a file."""

    repository_id: UUID
    file_path: str
    ref: Optional[str] = "main"


class BlameContextResponse(BaseModel):
    """Blame context with commit history."""

    line_number: int
    commit_sha: str
    commit_message: Optional[str]
    author: Optional[str]
    introduced_at: Optional[datetime]
    commit_data: Optional[dict] = None
