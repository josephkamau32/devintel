import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.organization import Organization, OrganizationMember
from app.models.repository import Repository

@pytest.fixture
async def organization(db_session: AsyncSession, test_user: dict):
    """Create a test organization"""
    user_id = test_user["id"]
    org_id = uuid4()
    
    org = Organization(
        id=org_id,
        name="Test Corp",
        slug="test-corp",
        created_by=user_id
    )
    db_session.add(org)
    
    member = OrganizationMember(
        org_id=org_id,
        user_id=user_id,
        role="owner"
    )
    db_session.add(member)
    await db_session.commit()
    
    return org

@pytest.fixture
async def organization_member(db_session: AsyncSession, organization: Organization, active_user: dict):
    """Create a second test user and add them as a member"""
    member = OrganizationMember(
        org_id=organization.id,
        user_id=active_user["id"],
        role="member"
    )
    db_session.add(member)
    await db_session.commit()
    return active_user

@pytest.mark.asyncio
async def test_create_organization(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.post(
        "/api/v1/organizations/",
        json={"name": "New Awesome Org"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Awesome Org"
    assert data["role"] == "owner"

@pytest.mark.asyncio
async def test_create_duplicate_organization_name(async_client: AsyncClient, auth_headers: dict, organization: Organization):
    response = await async_client.post(
        "/api/v1/organizations/",
        json={"name": "Test Corp"},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_user_organizations(async_client: AsyncClient, auth_headers: dict, organization: Organization):
    response = await async_client.get("/api/v1/organizations/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    org = next((o for o in data if o["id"] == str(organization.id)), None)
    assert org is not None
    assert org["name"] == "Test Corp"
    assert org["role"] == "owner"

@pytest.mark.asyncio
async def test_get_organization(async_client: AsyncClient, auth_headers: dict, organization: Organization):
    response = await async_client.get(f"/api/v1/organizations/{organization.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Corp"
    assert len(data["members"]) == 1

@pytest.mark.asyncio
async def test_invite_member(async_client: AsyncClient, auth_headers: dict, organization: Organization, active_user: dict):
    # active_user is the second user fixture
    response = await async_client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={"email": active_user["email"], "role": "admin"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(active_user["id"])
    assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_get_organization_unauthorized(async_client: AsyncClient, active_user_auth_headers: dict, organization: Organization):
    # active_user is not in the organization
    response = await async_client.get(f"/api/v1/organizations/{organization.id}", headers=active_user_auth_headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_repository_in_organization(async_client: AsyncClient, auth_headers: dict, organization: Organization):
    response = await async_client.post(
        "/api/v1/repos",
        json={
            "repo_name": "org-repo",
            "full_name": "testcorp/org-repo",
            "url": "https://github.com/testcorp/org-repo",
            "org_id": str(organization.id)
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["org_id"] == str(organization.id)
    assert data["user_id"] is None

@pytest.mark.asyncio
async def test_list_organization_repositories(async_client: AsyncClient, auth_headers: dict, organization: Organization, db_session: AsyncSession):
    # Create a repo in the org directly in DB
    repo = Repository(
        id=uuid4(),
        repo_name="org-repo",
        full_name="testcorp/org-repo",
        url="https://github.com/testcorp/org-repo",
        org_id=organization.id
    )
    db_session.add(repo)
    await db_session.commit()
    
    response = await async_client.get(f"/api/v1/repos?org_id={organization.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["repositories"][0]["org_id"] == str(organization.id)

@pytest.mark.asyncio
async def test_access_organization_repository_unauthorized(async_client: AsyncClient, active_user_auth_headers: dict, organization: Organization, db_session: AsyncSession):
    # Create a repo in the org
    repo = Repository(
        id=uuid4(),
        repo_name="org-repo",
        full_name="testcorp/org-repo",
        url="https://github.com/testcorp/org-repo",
        org_id=organization.id
    )
    db_session.add(repo)
    await db_session.commit()
    
    # Try to access it with a user who is not a member (active_user)
    response = await async_client.get(f"/api/v1/repos/{repo.id}", headers=active_user_auth_headers)
    assert response.status_code == 403
