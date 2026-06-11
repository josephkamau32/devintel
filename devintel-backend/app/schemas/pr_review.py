"""PR review schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PRReviewRequest(BaseModel):
    """PR review request schema."""

    repository_id: UUID = Field(..., description="Repository ID")
    pull_request_diff: Optional[str] = Field(default=None, description="PR diff content (optional if pr_number provided)")
    pr_number: Optional[int] = Field(default=None, description="GitHub PR number")
    pr_title: str = Field(..., description="PR title")
    pr_description: str = Field(default="", description="PR description")


class PRReviewResponse(BaseModel):
    """PR review response schema."""

    summary: str = Field(..., description="Overall assessment of the PR")
    potential_issues: list[str] = Field(default_factory=list, description="Potential issues found")
    refactoring_suggestions: list[str] = Field(
        default_factory=list, description="Refactoring suggestions"
    )
    security_warnings: list[str] = Field(default_factory=list, description="Security concerns")
    performance_notes: list[str] = Field(default_factory=list, description="Performance considerations")


class PullRequestResponse(BaseModel):
    """Pull request response schema."""

    number: int
    title: str
    state: str
    author: str
    author_avatar: Optional[str] = None
    created_at: str
    updated_at: str
    additions: int
    deletions: int
    url: str


class PullRequestListResponse(BaseModel):
    """Pull request list response schema."""

    pulls: list[PullRequestResponse]
    repository_id: UUID
