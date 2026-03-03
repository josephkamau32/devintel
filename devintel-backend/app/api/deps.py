"""API dependencies."""

from typing import List
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get current authenticated user."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization.replace("Bearer ", "")

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(UUID(user_id))

        if not user:
            raise AuthenticationError("User not found")

        return user

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


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
    from app.models.organization import OrganizationRole
    from app.services.organization_service import OrganizationService

    if required_roles is None:
        if write_access:
            # Only owners/admins may delete or perform destructive operations
            required_roles = [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        else:
            required_roles = [
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN,
                OrganizationRole.MEMBER,
            ]

    if repository.org_id:
        await OrganizationService.check_user_role(
            db, repository.org_id, current_user.id, required_roles
        )
    elif repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository",
        )

