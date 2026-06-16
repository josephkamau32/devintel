"""Test generation schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class GeneratedTestResponse(BaseModel):
    """Generated test response schema."""

    id: UUID
    repo_id: UUID
    draft_pr_id: Optional[UUID]
    file_path: str
    test_content: str
    status: str
    output: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestGenerateRequest(BaseModel):
    """Request to generate tests for a PR diff."""

    repository_id: UUID
    file_changes: list[dict[str, str]]


class TestGenerateResponse(BaseModel):
    """Response from test generation."""

    test_id: str
    passed: bool
    output: str


class TestListResult(BaseModel):
    """List tests result."""

    tests: list[GeneratedTestResponse]


class TestRegenerateRequest(BaseModel):
    """Request to regenerate tests."""

    repository_id: UUID
    test_id: UUID
    file_changes: list[dict[str, str]]