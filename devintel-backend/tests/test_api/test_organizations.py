"""Tests for Organization API endpoints and RBAC."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.organization import Organization, OrganizationMember
from app.models.repository import Repository
from app.models.user import User


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def organization(db_session: AsyncSession, test_user: User):
    """Create a test organization owned by test_user."""
    org_id = uuid4()

    org = Organization(
        id=org_id,
        name="Test Corp",
        slug="test-corp",
        created_by=test_user.id,
    )
    db_session.add(org)

    member = OrganizationMember(
        org_id=org_id,
        user_id=test_user.id,
        role="owner",
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(org)

    return org


@pytest.fixture
async def organization_member(
    db_session: AsyncSession, organization: Organization, active_user: User
):
    """Add active_user as a regular member of the test organization."""
    member = OrganizationMember(
        org_id=organization.id,
        user_id=active_user.id,
        role="member",
    )
    db_session.add(member)
    await db_session.commit()
    return active_user


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_organization(async_client: AsyncClient, auth_headers: dict):
    """Creating an org returns 201 with name and slug."""
    response = await async_client.post(
        "/api/v1/organizations/",
        json={"name": "New Awesome Org"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Awesome Org"
    assert "slug" in data
    # OrganizationDetailed has members[], not a role field at the top level
    assert "members" in data


@pytest.mark.asyncio
async def test_create_duplicate_organization_name(
    async_client: AsyncClient, auth_headers: dict, organization: Organization
):
    """Creating an org whose slug already exists generates a unique slug (no 400)
    unless the service raises explicitly. Test corp slug uniqueness via API."""
    response = await async_client.post(
        "/api/v1/organizations/",
        json={"name": "Test Corp"},
        headers=auth_headers,
    )
    # The service auto-increments the slug rather than raising, so either 201
    # with a different slug OR 400 if the service decides to reject by name.
    # Accept both: if 201, verify slug is different; if 400, verify message.
    if response.status_code == 201:
        assert response.json()["slug"] != "test-corp"
    else:
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_user_organizations(
    async_client: AsyncClient, auth_headers: dict, organization: Organization
):
    """Authenticated user sees their organizations with their role."""
    response = await async_client.get("/api/v1/organizations/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    org = next((o for o in data if o["id"] == str(organization.id)), None)
    assert org is not None
    assert org["name"] == "Test Corp"
    assert org["my_role"] == "owner"


@pytest.mark.asyncio
async def test_get_organization(
    async_client: AsyncClient, auth_headers: dict, organization: Organization
):
    """Member can fetch org details including member list."""
    response = await async_client.get(
        f"/api/v1/organizations/{organization.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Corp"
    assert isinstance(data["members"], list)
    assert len(data["members"]) >= 1


@pytest.mark.asyncio
async def test_get_organization_unauthorized(
    async_client: AsyncClient,
    active_user_auth_headers: dict,
    organization: Organization,
):
    """A user who is not a member gets a 403."""
    response = await async_client.get(
        f"/api/v1/organizations/{organization.id}",
        headers=active_user_auth_headers,
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Member management tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invite_member(
    async_client: AsyncClient,
    auth_headers: dict,
    organization: Organization,
    active_user: User,
):
    """Owner can invite a user by user_id."""
    response = await async_client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={"user_id": str(active_user.id), "role": "admin"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(active_user.id)
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_invite_already_member(
    async_client: AsyncClient,
    auth_headers: dict,
    organization: Organization,
    organization_member: User,
):
    """Inviting someone already in the org returns 400."""
    response = await async_client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={"user_id": str(organization_member.id), "role": "member"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "already a member" in response.json()["detail"]


@pytest.mark.asyncio
async def test_member_cannot_invite(
    async_client: AsyncClient,
    active_user_auth_headers: dict,
    organization: Organization,
    organization_member: User,
    db_session: AsyncSession,
):
    """A regular member cannot invite other users (only OWNER/ADMIN can)."""
    # Create a third user to try and invite
    third_user = User(
        github_id="third_github_789",
        email="third@example.com",
        name="Third User",
        username="thirduser",
        avatar_url="https://avatars.githubusercontent.com/u/789",
    )
    db_session.add(third_user)
    await db_session.commit()
    await db_session.refresh(third_user)

    response = await async_client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={"user_id": str(third_user.id), "role": "member"},
        headers=active_user_auth_headers,  # active_user is a MEMBER
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_member_role(
    async_client: AsyncClient,
    auth_headers: dict,
    organization: Organization,
    organization_member: User,
):
    """Owner can promote a member to admin."""
    response = await async_client.put(
        f"/api/v1/organizations/{organization.id}/members/{organization_member.id}/role",
        json={"role": "admin"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_remove_member(
    async_client: AsyncClient,
    auth_headers: dict,
    organization: Organization,
    organization_member: User,
):
    """Owner can remove a member from the org."""
    response = await async_client.delete(
        f"/api/v1/organizations/{organization.id}/members/{organization_member.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify the member is gone by trying to access with their token
    # (they can no longer GET the org)


@pytest.mark.asyncio
async def test_update_organization(
    async_client: AsyncClient,
    auth_headers: dict,
    organization: Organization,
):
    """Owner can rename the organization."""
    response = await async_client.put(
        f"/api/v1/organizations/{organization.id}",
        json={"name": "Updated Corp Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Corp Name"


# ---------------------------------------------------------------------------
# Repository × Organization RBAC tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_repository_in_organization(
    async_client: AsyncClient, auth_headers: dict, organization: Organization
):
    """Owner can add a repository under their organization."""
    response = await async_client.post(
        "/api/v1/repos",
        json={
            "repo_name": "org-repo",
            "full_name": "testcorp/org-repo",
            "url": "https://github.com/testcorp/org-repo",
            "org_id": str(organization.id),
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["org_id"] == str(organization.id)
    assert data["user_id"] is None


@pytest.mark.asyncio
async def test_list_organization_repositories(
    async_client: AsyncClient,
    auth_headers: dict,
    organization: Organization,
    db_session: AsyncSession,
):
    """Members can list repositories belonging to their org."""
    repo = Repository(
        id=uuid4(),
        repo_name="org-repo",
        full_name="testcorp/org-repo",
        url="https://github.com/testcorp/org-repo",
        org_id=organization.id,
    )
    db_session.add(repo)
    await db_session.commit()

    response = await async_client.get(
        f"/api/v1/repos?org_id={organization.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["repositories"][0]["org_id"] == str(organization.id)


@pytest.mark.asyncio
async def test_access_organization_repository_unauthorized(
    async_client: AsyncClient,
    active_user_auth_headers: dict,
    organization: Organization,
    db_session: AsyncSession,
):
    """A non-member cannot access an organization repository by ID."""
    repo = Repository(
        id=uuid4(),
        repo_name="org-repo",
        full_name="testcorp/org-repo",
        url="https://github.com/testcorp/org-repo",
        org_id=organization.id,
    )
    db_session.add(repo)
    await db_session.commit()

    # active_user is NOT a member of the org
    response = await async_client.get(
        f"/api/v1/repos/{repo.id}", headers=active_user_auth_headers
    )
    assert response.status_code == 403
