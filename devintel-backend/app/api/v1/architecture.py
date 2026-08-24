"""Architecture visualization API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.db.session import get_db
from app.models.repository import IndexingStatus
from app.models.user import User
from app.repositories.architecture import ArchitectureDiagramRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.architecture import (
    ArchitectureDiagramResponse,
    DiagramGenerateRequest,
    DiagramGenerateResponse,
    DiagramListResponse,
)
from app.services.architecture_service import ArchitectureVisualizationService

router = APIRouter(prefix="/architecture", tags=["Architecture"])


@router.post("/diagrams/generate", response_model=DiagramGenerateResponse)
async def generate_diagram(
    request: DiagramGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an architecture diagram for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    if repository.indexing_status != IndexingStatus.COMPLETE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository must be indexed first")

    service = ArchitectureVisualizationService(db)
    diagram = await service.generate_mermaid_diagram(
        repository=repository,
        diagram_type=request.diagram_type,
        focus_paths=request.focus_paths,
    )

    return DiagramGenerateResponse(diagram=ArchitectureDiagramResponse.model_validate(diagram))


@router.get("/diagrams/{repository_id}", response_model=DiagramListResponse)
async def list_diagrams(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all architecture diagrams for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    diagram_repo = ArchitectureDiagramRepository(db)
    diagrams = await diagram_repo.get_by_repo(repository_id)

    return DiagramListResponse(
        diagrams=[ArchitectureDiagramResponse.model_validate(d) for d in diagrams]
    )


@router.get("/diagrams/{diagram_id}", response_model=ArchitectureDiagramResponse)
async def get_diagram(
    diagram_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific architecture diagram."""
    diagram_repo = ArchitectureDiagramRepository(db)
    diagram = await diagram_repo.get_by_id(diagram_id)

    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagram not found")

    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(diagram.repo_id)
    await check_repo_access(repository, current_user, db)

    return ArchitectureDiagramResponse.model_validate(diagram)
