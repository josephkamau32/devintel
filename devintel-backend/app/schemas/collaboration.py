"""Collaboration schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CollaborationSessionCreate(BaseModel):
    """Create collaboration session request."""

    repository_id: UUID = Field(..., description="Repository to collaborate on")
    session_name: str = Field(..., min_length=1, max_length=255)


class CollaborationSessionResponse(BaseModel):
    """Collaboration session response."""

    id: UUID
    repo_id: UUID
    owner_id: UUID
    session_name: str
    is_active: bool
    participants_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollaborationMessageCreate(BaseModel):
    """Create message request."""

    session_id: UUID
    message_type: str = Field(..., pattern="^(text|cursor|code_change|ai_suggestion)$")
    content: str = Field(..., min_length=1)
    file_path: Optional[str] = None
    cursor_line: Optional[int] = None
    cursor_column: Optional[int] = None


class CollaborationMessageResponse(BaseModel):
    """Collaboration message response."""

    id: UUID
    session_id: UUID
    user_id: UUID
    message_type: str
    content: str
    file_path: Optional[str]
    cursor_line: Optional[int]
    cursor_column: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class CollaborationHistoryResponse(BaseModel):
    """Collaboration message history response."""

    messages: list[CollaborationMessageResponse]