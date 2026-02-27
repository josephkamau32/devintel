"""Organization API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationDetailed,
    OrganizationMemberCreate,
    OrganizationMemberRead,
    OrganizationMemberUpdate,
    OrganizationUpdate,
    OrganizationWithRole,
)
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.post("/", response_model=OrganizationDetailed, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organization."""
    return await OrganizationService.create_organization(db, org_in, current_user.id)


@router.get("/", response_model=List[OrganizationWithRole])
async def list_user_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all organizations the user is a member of."""
    return await OrganizationService.get_user_organizations(db, current_user.id)


@router.get("/{org_id}", response_model=OrganizationDetailed)
async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get organization details (requires membership)."""
    # Simply checking the role ensures they are a member
    await OrganizationService.check_user_role(
        db, org_id, current_user.id, ["owner", "admin", "member"]
    )
    
    org = await OrganizationService.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/{org_id}", response_model=OrganizationDetailed)
async def update_organization(
    org_id: UUID,
    org_update: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update organization details (requires OWNER or ADMIN)."""
    return await OrganizationService.update_organization(db, org_id, current_user.id, org_update)


@router.get("/{org_id}/members", response_model=List[OrganizationMemberRead])
async def list_organization_members(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all members of an organization."""
    members = await OrganizationService.get_organization_members(db, org_id, current_user.id)
    # Populate extra fields for response manually since joinedload doesn't auto-flatten
    result = []
    for m in members:
        # Pydantic will serialize this directly if we assign it
        m.username = m.user.username if m.user else None
        m.email = m.user.email if m.user else None
        m.name = m.user.name if m.user else None
        m.avatar_url = m.user.avatar_url if m.user else None
        result.append(m)
        
    return result


@router.post("/{org_id}/members", response_model=OrganizationMemberRead)
async def add_organization_member(
    org_id: UUID,
    member_in: OrganizationMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite/Add a user to the organization by user_id."""
    if not member_in.user_id:
        raise HTTPException(status_code=400, detail="Must provide user_id to invite")
        
    member = await OrganizationService.add_member(
        db, org_id, current_user.id, member_in.user_id, member_in.role
    )
    # Reload to get user details
    members = await OrganizationService.get_organization_members(db, org_id, current_user.id)
    for m in members:
        if m.user_id == member_in.user_id:
            m.username = m.user.username if m.user else None
            m.email = m.user.email if m.user else None
            m.name = m.user.name if m.user else None
            m.avatar_url = m.user.avatar_url if m.user else None
            return m
    return member


@router.put("/{org_id}/members/{user_id}/role", response_model=OrganizationMemberRead)
async def update_member_role(
    org_id: UUID,
    user_id: UUID,
    role_update: OrganizationMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user's role in the organization."""
    member = await OrganizationService.update_member_role(
        db, org_id, current_user.id, user_id, role_update.role
    )
    # Provide simple read object
    return member


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a user from the organization."""
    await OrganizationService.remove_member(db, org_id, current_user.id, user_id)
    return None
