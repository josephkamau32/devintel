"""Code migration schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MigrationProjectCreate(BaseModel):
    """Create migration project request."""

    repository_id: UUID = Field(..., description="Repository to migrate")
    source_tech: str = Field(..., min_length=1, max_length=100, description="Source technology")
    target_tech: str = Field(..., min_length=1, max_length=100, description="Target technology")


class MigrationProjectResponse(BaseModel):
    """Migration project response."""

    id: UUID
    repo_id: UUID
    source_tech: str
    target_tech: str
    status: str
    progress_percent: int
    migration_plan: Optional[str]
    migrated_files: int
    total_files: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MigratedFileResponse(BaseModel):
    """Migrated file response."""

    id: UUID
    project_id: UUID
    original_path: str
    migrated_path: str
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MigrationStatusResponse(BaseModel):
    """Migration status response."""

    project: MigrationProjectResponse
    migrated_files: list[MigratedFileResponse]
