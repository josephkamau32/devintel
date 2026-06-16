"""Policy routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.models.user import User
from app.models.policy import PolicyRuleType, PolicySeverity
from app.repositories.policy import PolicyRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.policy import (
    PolicyCreate,
    PolicyResponse,
    PolicyListResponse,
    PolicyCheckRequest,
    PolicyCheckResponse,
)

router = APIRouter(prefix="/repos", tags=["Policies"])


@router.get("/{repository_id}/policies", response_model=PolicyListResponse)
async def list_policies(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List policies for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    policy_repo = PolicyRepository(db)
    policies = await policy_repo.get_by_repo(repository_id)

    return PolicyListResponse(policies=policies, repository_id=repository_id)


@router.post("/{repository_id}/policies", response_model=PolicyResponse)
async def create_policy(
    repository_id: UUID,
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a policy rule."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db, write_access=True)

    policy_repo = PolicyRepository(db)
    policy = await policy_repo.create(
        repo_id=repository_id,
        name=policy_data.name,
        description=policy_data.description,
        rule_type=policy_data.rule_type,
        config=policy_data.config,
        severity=policy_data.severity,
    )

    await db.commit()
    return PolicyResponse.model_validate(policy)


@router.put("/{repository_id}/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    repository_id: UUID,
    policy_id: UUID,
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a policy rule."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db, write_access=True)

    policy_repo = PolicyRepository(db)
    policy = await policy_repo.get_by_id(policy_id)

    if not policy or policy.repo_id != repository_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    updated = await policy_repo.update(
        policy_id,
        name=policy_data.name,
        description=policy_data.description,
        config=policy_data.config,
        severity=policy_data.severity,
    )
    await db.commit()
    return PolicyResponse.model_validate(updated)


@router.delete("/{repository_id}/policies/{policy_id}")
async def delete_policy(
    repository_id: UUID,
    policy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a policy rule."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db, write_access=True)

    policy_repo = PolicyRepository(db)
    await policy_repo.delete(policy_id)
    await db.commit()

    return {"message": "Policy deleted successfully"}


@router.post("/{repository_id}/policies/check", response_model=PolicyCheckResponse)
async def check_policies(
    repository_id: UUID,
    request: PolicyCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check a diff against repository policies."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    from app.services.policy_service import PolicyChecker
    checker = PolicyChecker(db)
    violations = await checker.check(request.diff, repository_id)

    return PolicyCheckResponse(
        violations=violations,
        passed=len([v for v in violations if v.severity == "error"]) == 0,
    )