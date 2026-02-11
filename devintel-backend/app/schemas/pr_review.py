"""PR review schemas."""

from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class PRReviewRequest(BaseModel):
    """PR review request schema."""

    repository_id: UUID = Field(..., description="Repository ID")
    pull_request_diff: str = Field(..., min_length=1, description="PR diff content")
    pr_title: str = Field(..., description="PR title")
    pr_description: str = Field(default="", description="PR description")


class PRReviewResponse(BaseModel):
    """PR review response schema."""

    summary: str = Field(..., description="Overall assessment of the PR")
    potential_issues: List[str] = Field(default_factory=list, description="Potential issues found")
    refactoring_suggestions: List[str] = Field(
        default_factory=list, description="Refactoring suggestions"
    )
    security_warnings: List[str] = Field(default_factory=list, description="Security concerns")
    performance_notes: List[str] = Field(default_factory=list, description="Performance considerations")
