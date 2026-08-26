"""Comprehensive tests for repository authorization and RBAC (F-05)."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access
from app.core.security import create_access_token
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.repository import Repository
from app.models.user import User


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def org_alpha(db_session: AsyncSession, test_user: User) -> Organization:
    """Create Organization Alpha owned by test_user."""
    org_id = uuid4()
    org = Organization(
        id=org_id,
        name="Alpha Org",
        slug="alpha-org",
        created_by=test_user.id,
    )
    db_session.add(org)

    owner_member = OrganizationMember(
        org_id=org_id,
        user_id=test_user.id,
        role=OrganizationRole.OWNER,
    )
    db_session.add(owner_member)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_beta(db_session: AsyncSession) -> Organization:
    """Create an unrelated Organization Beta."""
    beta_owner = User(
        id=uuid4(),
        email="beta_owner@example.com",
        full_name="Beta Owner",
        github_username="betaowner",
    )
    db_session.add(beta_owner)
    await db_session.flush()

    org_id = uuid4()
    org = Organization(
        id=org_id,
        name="Beta Org",
        slug="beta-org",
        created_by=beta_owner.id,
    )
    db_session.add(org)

    owner_member = OrganizationMember(
        org_id=org_id,
        user_id=beta_owner.id,
        role=OrganizationRole.OWNER,
    )
    db_session.add(owner_member)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def member_user(db_session: AsyncSession, org_alpha: Organization) -> tuple[User, dict]:
    """Create a user who is a regular MEMBER in Org Alpha."""
    user = User(
        id=uuid4(),
        email="member@alpha.com",
        full_name="Alpha Member",
        github_username="alphamember",
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMember(
        org_id=org_alpha.id,
        user_id=user.id,
        role=OrganizationRole.MEMBER,
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


@pytest.fixture
async def admin_user(db_session: AsyncSession, org_alpha: Organization) -> tuple[User, dict]:
    """Create a user who is an ADMIN in Org Alpha."""
    user = User(
        id=uuid4(),
        email="admin@alpha.com",
        full_name="Alpha Admin",
        github_username="alphaadmin",
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMember(
        org_id=org_alpha.id,
        user_id=user.id,
        role=OrganizationRole.ADMIN,
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


@pytest.fixture
async def unrelated_user(db_session: AsyncSession, org_beta: Organization) -> tuple[User, dict]:
    """Create a user who is a member of Beta Org, but NOT Alpha Org."""
    user = User(
        id=uuid4(),
        email="unrelated@beta.com",
        full_name="Beta Member",
        github_username="betamember",
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMember(
        org_id=org_beta.id,
        user_id=user.id,
        role=OrganizationRole.MEMBER,
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


@pytest.fixture
async def alpha_org_repo(
    db_session: AsyncSession, org_alpha: Organization, test_user: User
) -> Repository:
    """Create a repository belonging to Org Alpha, added by test_user (Owner)."""
    repo = Repository(
        id=uuid4(),
        user_id=test_user.id,
        repo_name="alpha-repo",
        full_name="alpha/alpha-repo",
        url="https://github.com/alpha/alpha-repo",
        organization_id=org_alpha.id,
        indexing_status="pending",
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)
    return repo


# ---------------------------------------------------------------------------
# Direct Unit Tests on check_repo_access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_repo_access_personal_repo_owner_allowed(
    db_session: AsyncSession, test_user: User
):
    """Personal repo: owner is permitted."""
    repo = Repository(
        id=uuid4(),
        user_id=test_user.id,
        repo_name="personal-repo",
        full_name="user/personal-repo",
        organization_id=None,
    )
    # Should not raise
    await check_repo_access(repo, test_user, db_session)
    await check_repo_access(repo, test_user, db_session, write_access=True)


@pytest.mark.asyncio
async def test_check_repo_access_personal_repo_non_owner_denied(
    db_session: AsyncSession, test_user: User, member_user: tuple[User, dict]
):
    """Personal repo: non-owner gets 403."""
    user, _ = member_user
    repo = Repository(
        id=uuid4(),
        user_id=test_user.id,
        repo_name="personal-repo",
        full_name="user/personal-repo",
        organization_id=None,
    )
    with pytest.raises(HTTPException) as exc_info:
        await check_repo_access(repo, user, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_check_repo_access_org_member_read_allowed_write_denied(
    db_session: AsyncSession, alpha_org_repo: Repository, member_user: tuple[User, dict]
):
    """Org repo: regular MEMBER can read, but gets 403 on write_access=True."""
    user, _ = member_user
    # Read access -> allowed
    await check_repo_access(alpha_org_repo, user, db_session, write_access=False)

    # Write access -> denied
    with pytest.raises(HTTPException) as exc_info:
        await check_repo_access(alpha_org_repo, user, db_session, write_access=True)
    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in exc_info.value.detail


@pytest.mark.asyncio
async def test_check_repo_access_org_admin_both_allowed(
    db_session: AsyncSession, alpha_org_repo: Repository, admin_user: tuple[User, dict]
):
    """Org repo: ADMIN has both read and write access."""
    user, _ = admin_user
    await check_repo_access(alpha_org_repo, user, db_session, write_access=False)
    await check_repo_access(alpha_org_repo, user, db_session, write_access=True)


@pytest.mark.asyncio
async def test_check_repo_access_unrelated_org_member_denied(
    db_session: AsyncSession, alpha_org_repo: Repository, unrelated_user: tuple[User, dict]
):
    """Org repo: member of another org is denied read and write."""
    user, _ = unrelated_user
    with pytest.raises(HTTPException) as exc_info_read:
        await check_repo_access(alpha_org_repo, user, db_session, write_access=False)
    assert exc_info_read.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info_write:
        await check_repo_access(alpha_org_repo, user, db_session, write_access=True)
    assert exc_info_write.value.status_code == 403


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_org_member_can_view_repo_detail(
    async_client: AsyncClient,
    alpha_org_repo: Repository,
    member_user: tuple[User, dict],
):
    """Org member can view details of an org repo via GET /repos/{id}."""
    _, headers = member_user
    response = await async_client.get(f"/api/v1/repos/{alpha_org_repo.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(alpha_org_repo.id)
    assert data["full_name"] == alpha_org_repo.full_name


@pytest.mark.asyncio
async def test_org_member_cannot_delete_org_repo(
    async_client: AsyncClient,
    alpha_org_repo: Repository,
    member_user: tuple[User, dict],
):
    """Org member (role=MEMBER) cannot delete org repo (requires OWNER or ADMIN)."""
    _, headers = member_user
    response = await async_client.delete(f"/api/v1/repos/{alpha_org_repo.id}", headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_org_member_cannot_create_policy(
    async_client: AsyncClient,
    alpha_org_repo: Repository,
    member_user: tuple[User, dict],
):
    """Org member (role=MEMBER) cannot create policies (requires OWNER or ADMIN)."""
    _, headers = member_user
    response = await async_client.post(
        f"/api/v1/repos/{alpha_org_repo.id}/policies",
        json={
            "name": "No console.log",
            "rule_type": "disallowed_pattern",
            "severity": "warning",
            "config": {"pattern": "console\\.log"},
        },
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_org_admin_can_create_policy_and_read(
    async_client: AsyncClient,
    alpha_org_repo: Repository,
    admin_user: tuple[User, dict],
):
    """Org admin (role=ADMIN) can create policies and read them."""
    _, headers = admin_user
    # 1. Create policy (write)
    create_res = await async_client.post(
        f"/api/v1/repos/{alpha_org_repo.id}/policies",
        json={
            "name": "No secrets",
            "rule_type": "disallowed_pattern",
            "severity": "error",
            "config": {"pattern": "SECRET_KEY"},
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    policy_data = create_res.json()
    assert policy_data["name"] == "No secrets"

    # 2. List policies (read)
    list_res = await async_client.get(
        f"/api/v1/repos/{alpha_org_repo.id}/policies", headers=headers
    )
    assert list_res.status_code == 200
    assert len(list_res.json()["policies"]) >= 1


@pytest.mark.asyncio
async def test_revocation_member_removal_immediately_denies_access(
    async_client: AsyncClient,
    db_session: AsyncSession,
    org_alpha: Organization,
    alpha_org_repo: Repository,
    member_user: tuple[User, dict],
):
    """Live revocation test: Removing an OrganizationMember row immediately revokes access."""
    user, headers = member_user

    # Request 1: Member has access
    res1 = await async_client.get(f"/api/v1/repos/{alpha_org_repo.id}", headers=headers)
    assert res1.status_code == 200

    # Simulate member removal (delete row from organization_members)
    member_row = await db_session.get(OrganizationMember, (org_alpha.id, user.id))
    assert member_row is not None
    await db_session.delete(member_row)
    await db_session.commit()

    # Request 2: Next immediate request must be DENIED (HTTP 403)
    res2 = await async_client.get(f"/api/v1/repos/{alpha_org_repo.id}", headers=headers)
    assert res2.status_code == 403
    assert "Not authorized" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_revocation_original_adder_removal_denies_access(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    org_alpha: Organization,
    alpha_org_repo: Repository,
    test_user: User,
):
    """
    Critical security test: The original adder of an org repo (where repository.user_id == user.id)
    loses access when removed from OrganizationMember. No special-casing for original adder.
    """
    assert alpha_org_repo.user_id == test_user.id

    # Request 1: Original adder (Owner) has access
    res1 = await async_client.get(f"/api/v1/repos/{alpha_org_repo.id}", headers=auth_headers)
    assert res1.status_code == 200

    # Simulate original adder being removed from the organization
    member_row = await db_session.get(OrganizationMember, (org_alpha.id, test_user.id))
    assert member_row is not None
    await db_session.delete(member_row)
    await db_session.commit()

    # Request 2: Original adder must be DENIED access now that membership is revoked
    res2 = await async_client.get(f"/api/v1/repos/{alpha_org_repo.id}", headers=auth_headers)
    assert res2.status_code == 403
    assert "Not authorized" in res2.json()["detail"]

    # Direct unit guard check
    with pytest.raises(HTTPException) as exc_info:
        await check_repo_access(alpha_org_repo, test_user, db_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_personal_repo_owner_access_no_org_check(
    async_client: AsyncClient,
    auth_headers: dict,
    test_user: User,
    member_user: tuple[User, dict],
    db_session: AsyncSession,
):
    """
    Personal repository (organization_id is None): Owner retains access without org lookup;
    non-owner is denied access.
    """
    personal_repo = Repository(
        id=uuid4(),
        user_id=test_user.id,
        repo_name="personal-standalone",
        full_name="testuser/personal-standalone",
        url="https://github.com/testuser/personal-standalone",
        organization_id=None,
    )
    db_session.add(personal_repo)
    await db_session.commit()

    # Owner can access
    res_owner = await async_client.get(f"/api/v1/repos/{personal_repo.id}", headers=auth_headers)
    assert res_owner.status_code == 200

    # Non-owner is denied
    _, other_headers = member_user
    res_other = await async_client.get(f"/api/v1/repos/{personal_repo.id}", headers=other_headers)
    assert res_other.status_code == 403


# ---------------------------------------------------------------------------
# WebSocket Authorization Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_websocket_org_member_access_and_unrelated_rejection(
    db_session: AsyncSession,
    org_alpha: Organization,
    alpha_org_repo: Repository,
    member_user: tuple[User, dict],
    unrelated_user: tuple[User, dict],
):
    """
    WebSocket authorization check (/ws/repos/{repo_id}/progress):
    1. Org member (not the repo adder) is permitted and connects.
    2. Unrelated user with no org membership is rejected with {"error": "Not authorized"}.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from fastapi.testclient import TestClient
    from app.main import app

    member_u, _ = member_user
    unrelated_u, _ = unrelated_user

    member_token = create_access_token(member_u.id)
    unrelated_token = create_access_token(unrelated_u.id)

    mock_db_cm = MagicMock()
    mock_db_cm.__aenter__ = AsyncMock(return_value=db_session)
    mock_db_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.v1.ws.AsyncSessionLocal", return_value=mock_db_cm):
        client = TestClient(app, raise_server_exceptions=False)

        # 1. Org member who is NOT the repo's original adder connects successfully
        with client.websocket_connect(
            f"/api/v1/ws/repos/{alpha_org_repo.id}/progress?token={member_token}"
        ) as ws:
            msg = ws.receive_json()
            # Message should be initial progress status, NOT authorization error
            assert msg.get("error") != "Not authorized"
            assert msg.get("status") in ("connecting", "done", "pending")

        # 2. Unrelated user with NO membership in org_alpha is rejected
        with client.websocket_connect(
            f"/api/v1/ws/repos/{alpha_org_repo.id}/progress?token={unrelated_token}"
        ) as ws:
            msg = ws.receive_json()
            assert msg.get("error") == "Not authorized"


