"""Chat schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    """A single message in chat history."""

    role: str = Field(..., pattern="^(user|assistant)$", description="Message role")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")


class ChatRequest(BaseModel):
    """Chat request schema."""

    repository_id: UUID = Field(..., description="Repository ID to query")
    question: str = Field(..., min_length=1, max_length=2000, description="User question")
    chat_history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        max_length=20,
        description="Previous chat messages for multi-turn context (max 20)",
    )


class ChatResponse(BaseModel):
    """Chat response schema."""

    id: UUID
    repository_id: UUID
    question: str
    response: str
    token_usage: int
    response_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ChatHistoryRecord(BaseModel):
    """Record retrieved from database."""

    role: str
    content: str
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history response schema."""

    messages: list[ChatHistoryRecord]
    repository_id: UUID


class StreamChunk(BaseModel):
    """Stream chunk schema for SSE."""

    content: str
    done: bool = False
