"""API dependencies."""

from collections.abc import Collection
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_current_user_optional  # noqa: F401
from app.models.organization import OrganizationMember, OrganizationRole
from app.models.user import User


async def check_repo_access(
    repository,
    current_user: User,
    db: AsyncSession,
    required_roles: Optional[Collection[OrganizationRole | str]] = None,
    *,
    write_access: bool = False,
) -> None:
    """
    Shared repository access guard used by all endpoints.

    - Personal repo (repository.organization_id is None):
        - Allowed if repository.user_id == current_user.id.
        - Otherwise 403 Forbidden.
    - Org repo (repository.organization_id is set):
        - ALWAYS checks OrganizationMember in DB (no shortcut for original adder).
        - If no row found: 403 Forbidden ("Not authorized to access this repository").
        - If row found: checks role against requirements:
            - If required_roles is provided: role must be in required_roles.
            - Else if write_access=True: role must be OWNER or ADMIN.
            - Else (default write_access=False): OWNER, ADMIN, or MEMBER allowed.
    """
    # 1. Personal repository: user must be the owner
    if repository.organization_id is None:
        if repository.user_id == current_user.id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository",
        )

    # 2. Organization-owned repository: ALWAYS perform live membership lookup
    stmt = select(OrganizationMember).where(
        OrganizationMember.org_id == repository.organization_id,
        OrganizationMember.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository",
        )

    if required_roles is not None:
        allowed = {
            r.value if isinstance(r, OrganizationRole) else str(r)
            for r in required_roles
        }
        member_role_val = (
            member.role.value
            if isinstance(member.role, OrganizationRole)
            else str(member.role)
        )
        if member_role_val not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions in this organization",
            )
        return

    if write_access:
        member_role_val = (
            member.role.value
            if isinstance(member.role, OrganizationRole)
            else str(member.role)
        )
        if member_role_val not in {
            OrganizationRole.OWNER.value,
            OrganizationRole.ADMIN.value,
            "owner",
            "admin",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions in this organization",
            )
        return

    # Read access with no explicit role requirements: any valid member is permitted
    return
