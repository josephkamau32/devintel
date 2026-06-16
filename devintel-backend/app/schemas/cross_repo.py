"""Cross-repository knowledge schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CrossRepoPatternRequest(BaseModel):
    """Request to find cross-repository patterns."""

    repository_id: UUID = Field(..., description="Source repository ID")
    pattern_type: str = Field(
        ...,
        description="Pattern type to search: architecture, security, testing, performance"
    )
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(10, ge=1, le=50, description="Number of results")


class PatternMatch(BaseModel):
    """A pattern match from another repository."""

    repo_id: str = Field(..., description="Repository ID")
    file_path: str = Field(..., description="File path with similar pattern")
    chunk_text: str = Field(..., description="Code snippet")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    pattern_type: str = Field(..., description="Pattern type")


class CrossRepoPatternResponse(BaseModel):
    """Response with pattern matches."""

    patterns: list[PatternMatch]