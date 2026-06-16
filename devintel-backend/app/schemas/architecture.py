"""Architecture diagram schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ArchitectureDiagramResponse(BaseModel):
    """Architecture diagram response."""

    id: UUID
    repo_id: UUID
    name: str
    diagram_type: str
    mermaid_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiagramGenerateRequest(BaseModel):
    """Request to generate a diagram."""

    repository_id: UUID = Field(..., description="Repository to analyze")
    diagram_type: str = Field(
        "mermaid",
        description="Diagram type: mermaid, c4_context, c4_container, c4_component"
    )
    focus_paths: Optional[list[str]] = Field(
        None,
        description="Optional file paths to focus on"
    )


class DiagramGenerateResponse(BaseModel):
    """Response from diagram generation."""

    diagram: ArchitectureDiagramResponse


class DiagramListResponse(BaseModel):
    """List of diagrams response."""

    diagrams: list[ArchitectureDiagramResponse]