"""Organization service for business logic."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)

logger = logging.getLogger(__name__)


class OrganizationService:
    """Service for managing organizations and memberships."""

    @staticmethod
    async def create_organization(
        db: AsyncSession, org_create: OrganizationCreate, user_id: UUID
    ) -> Organization:
        """Create a new organization and set the creator as the OWNER."""
        # Generate slug
        base_slug = org_create.name.lower().replace(" ", "-")
        slug = base_slug
        counter = 1

        # Ensure slug is unique
        while True:
            result = await db.execute(select(Organization).where(Organization.slug == slug))
            if not result.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(
            name=org_create.name,
            slug=slug,
            created_by=user_id,
        )
        db.add(org)
        await db.flush()  # To get the org.id

        # Add creator as OWNER
        member = OrganizationMember(
            org_id=org.id,
            user_id=user_id,
            role=OrganizationRole.OWNER,
        )
        db.add(member)
        await db.commit()

        # Re-fetch with joinedload so that `members` relationship is available
        # (the model uses lazy='raise' which would break serialization)
        loaded_org = await OrganizationService.get_organization(db, org.id)
        return loaded_org

    @staticmethod
    async def get_organization(db: AsyncSession, org_id: UUID) -> Optional[Organization]:
        """Get an organization by ID."""
        result = await db.execute(
            select(Organization)
            .options(joinedload(Organization.members).joinedload(OrganizationMember.user))
            .where(Organization.id == org_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_user_organizations(db: AsyncSession, user_id: UUID) -> list[Organization]:
        """Get all organizations the user is a member of."""
        result = await db.execute(
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .where(OrganizationMember.user_id == user_id)
        )

        # We want to return the Organization objects, but we need to know the user's role in it
        members = result.scalars().all()
        orgs = []
        for member in members:
            # We can attach the role to the org object dynamically for serialization
            org = await OrganizationService.get_organization(db, member.org_id)
            if org:
                # Add a custom attribute that will be matched by `OrganizationWithRole` schema
                org.my_role = member.role
                orgs.append(org)

        return orgs

    @staticmethod
    async def check_user_role(
        db: AsyncSession, org_id: UUID, user_id: UUID, required_roles: list[OrganizationRole]
    ) -> OrganizationMember:
        """Check if a user has one of the required roles in an organization. Raises 403 if not."""
        result = await db.execute(
            select(OrganizationMember)
            .where(
                OrganizationMember.org_id == org_id,
                OrganizationMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this organization")

        if member.role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions in this organization")

        return member

    @staticmethod
    async def update_organization(
        db: AsyncSession, org_id: UUID, user_id: UUID, org_update: OrganizationUpdate
    ) -> Organization:
        """Update organization details (requires OWNER or ADMIN)."""
        await OrganizationService.check_user_role(
            db, org_id, user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        )

        org = await OrganizationService.get_organization(db, org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if org_update.name is not None:
            org.name = org_update.name

        await db.commit()
        # Re-fetch with joinedload so that `members` relationship is available
        loaded_org = await OrganizationService.get_organization(db, org_id)
        return loaded_org

    @staticmethod
    async def add_member(
        db: AsyncSession,
        org_id: UUID,
        admin_user_id: UUID,
        target_user_id: UUID,
        role: OrganizationRole = OrganizationRole.MEMBER
    ) -> OrganizationMember:
        """Add a member to an organization (requires OWNER or ADMIN)."""
        # Specific role check
        admin_member = await OrganizationService.check_user_role(
            db, org_id, admin_user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        )

        # Only owners can add other owners or admins
        if role in [OrganizationRole.OWNER, OrganizationRole.ADMIN] and admin_member.role != OrganizationRole.OWNER:
            raise HTTPException(status_code=403, detail="Only owners can assign admin or owner roles")

        # Check if already a member
        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.org_id == org_id,
                OrganizationMember.user_id == target_user_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="User is already a member")

        new_member = OrganizationMember(
            org_id=org_id,
            user_id=target_user_id,
            role=role
        )
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)
        return new_member

    @staticmethod
    async def get_organization_members(
        db: AsyncSession, org_id: UUID, user_id: UUID
    ) -> list[OrganizationMember]:
        """Get all members of an organization (requires being a member)."""
        await OrganizationService.check_user_role(
            db, org_id, user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER]
        )

        result = await db.execute(
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .where(OrganizationMember.org_id == org_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_member_role(
        db: AsyncSession,
        org_id: UUID,
        admin_user_id: UUID,
        target_user_id: UUID,
        new_role: OrganizationRole
    ) -> OrganizationMember:
        """Update a member's role (requires OWNER)."""
        await OrganizationService.check_user_role(
            db, org_id, admin_user_id, [OrganizationRole.OWNER]
        )

        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.org_id == org_id,
                OrganizationMember.user_id == target_user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        # Prevent last owner from removing their own owner status
        if member.role == OrganizationRole.OWNER and new_role != OrganizationRole.OWNER:
            owner_count_res = await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.org_id == org_id,
                    OrganizationMember.role == OrganizationRole.OWNER
                )
            )
            owners = owner_count_res.scalars().all()
            if len(owners) <= 1:
                raise HTTPException(status_code=400, detail="Organization must have at least one owner")

        member.role = new_role
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession, org_id: UUID, admin_user_id: UUID, target_user_id: UUID
    ):
        """Remove a member (requires OWNER or ADMIN, or self-leave)."""
        if admin_user_id != target_user_id:
            await OrganizationService.check_user_role(
                db, org_id, admin_user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN]
            )

        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.org_id == org_id,
                OrganizationMember.user_id == target_user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        if member.role == OrganizationRole.OWNER:
            owner_count_res = await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.org_id == org_id,
                    OrganizationMember.role == OrganizationRole.OWNER
                )
            )
            owners = owner_count_res.scalars().all()
            if len(owners) <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last owner of the organization")

        await db.delete(member)
        await db.commit()
        return {"success": True}
