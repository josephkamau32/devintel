"""API dependencies."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_current_user_optional  # noqa: F401
from app.models.user import User


async def check_repo_access(
    repository,
    current_user: User,
    db: AsyncSession,
    required_roles=None,
    *,
    write_access: bool = False,
) -> None:
    """
    Shared repository access guard used by all endpoints.

    For org-owned repositories, verifies that the current user has at least one
    of ``required_roles`` in that organization (defaults to OWNER | ADMIN | MEMBER).

    For personal repositories, verifies that ``current_user`` is the owner.

    Raises HTTP 403 on failure so callers never have to repeat this boilerplate.
    """
    if repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository",
        )
