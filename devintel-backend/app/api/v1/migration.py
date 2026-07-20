"""Code migration API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.migration import MigratedFileRepository, MigrationProjectRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.migration import (
    MigratedFileResponse,
    MigrationProjectCreate,
    MigrationProjectResponse,
    MigrationStatusResponse,
)
from app.services.migration_service import CodeMigrationService

router = APIRouter(prefix="/migration", tags=["Migration"])


@router.post("/projects", response_model=MigrationProjectResponse)
async def create_migration(
    request: MigrationProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new migration project."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    service = CodeMigrationService(db)
    project = await service.create_migration_project(
        repository=repository,
        source_tech=request.source_tech,
        target_tech=request.target_tech,
    )

    return MigrationProjectResponse.model_validate(project)


@router.post("/projects/{project_id}/plan")
async def generate_migration_plan(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate migration plan for a project."""
    project_repo = MigrationProjectRepository(db)
    project = await project_repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Migration project not found")

    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(project.repo_id)
    await check_repo_access(repository, current_user, db)

    service = CodeMigrationService(db)
    plan = await service.generate_migration_plan(project, repository)

    return {"plan": plan}


@router.get("/projects/{repository_id}", response_model=MigrationStatusResponse)
async def get_migration_status(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get migration status for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    project_repo = MigrationProjectRepository(db)
    project = await project_repo.get_active(repository_id)

    if not project:
        # Return empty state
        return MigrationStatusResponse(
            project=MigrationProjectResponse(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                repo_id=repository_id,
                source_tech="",
                target_tech="",
                status="none",
                progress_percent=0,
                migration_plan=None,
                migrated_files=0,
                total_files=0,
                created_at=None,
                updated_at=None,
            ),
            migrated_files=[],
        )

    migrated_repo = MigratedFileRepository(db)
    files = await migrated_repo.get_by_project(project.id)

    return MigrationStatusResponse(
        project=MigrationProjectResponse.model_validate(project),
        migrated_files=[MigratedFileResponse.model_validate(f) for f in files],
    )
