"""Policy schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    """Policy creation schema."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    rule_type: str = Field(..., description="Rule type: max_complexity, no_pattern, require_pattern, max_file_lines, require_docstrings, custom_prompt")
    config: dict = Field(default_factory=dict)
    severity: str = Field(default="warning", description="error or warning")


class PolicyResponse(PolicyCreate):
    """Policy response schema."""

    id: UUID
    repo_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolicyListResponse(BaseModel):
    """List policies response."""

    policies: list[PolicyResponse]
    repository_id: UUID


class PolicyViolation(BaseModel):
    """A policy violation."""

    rule_name: str
    rule_type: str
    severity: str
    file_path: str
    line_number: Optional[int]
    description: str
    suggestion: Optional[str]


class PolicyCheckRequest(BaseModel):
    """Policy check request."""

    diff: str = Field(..., min_length=1)


class PolicyCheckResponse(BaseModel):
    """Policy check response."""

    violations: list[PolicyViolation]
    passed: bool
