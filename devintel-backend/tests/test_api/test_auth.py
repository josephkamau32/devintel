"""Comprehensive authentication API tests."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


@pytest.mark.asyncio
async def test_signup_success(async_client: AsyncClient):
    """Test successful user registration."""
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword1",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_signup_duplicate_email(async_client: AsyncClient):
    """Test signup with existing email fails."""
    # First signup — must use a schema-valid password (uppercase + digit + ≥8 chars)
    first_response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "Password1",
            "full_name": "User One",
        },
    )
    assert first_response.status_code == 201  # Ensure first signup succeeds

    # Duplicate signup with the same email
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "Password2",
            "full_name": "User Two",
        },
    )
    assert response.status_code == 409  # ConflictError
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_signup_weak_password(async_client: AsyncClient):
    """Test signup with password shorter than 8 characters fails."""
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "weakpass@example.com",
            "password": "short",
            "full_name": "Weak Password User",
        },
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: User):
    """Test successful login with valid credentials.

    The test_user fixture already creates a user with email 'test@example.com'
    and hashed password for 'testpassword123'. We login with those credentials.
    """
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, test_user: User):
    """Test login with invalid password fails."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with nonexistent email fails."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh(async_client: AsyncClient, test_user: User):
    """Test token refresh endpoint.

    The refresh endpoint reads the refresh token from an HTTP-only cookie,
    not from the JSON body. We must create a proper *refresh* token (not an
    access token) and send it via the cookie.
    """
    refresh_tok = create_refresh_token(test_user.id)

    # Send the refresh token as a cookie (the endpoint reads from Cookie)
    response = await async_client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_tok},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_token_refresh_invalid_token(async_client: AsyncClient):
    """Test refresh with invalid token fails."""
    response = await async_client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": "invalid.token.string"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_github_login_redirect_sets_cookie_and_pkce(async_client: AsyncClient):
    """Test that GET /auth/github sets the oauth_state cookie and includes PKCE params."""
    response = await async_client.get("/api/v1/auth/github", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert "code_challenge=" in location
    assert "code_challenge_method=S256" in location
    assert "state=" in location

    # Verify oauth_state cookie was set
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "oauth_state=" in set_cookie_header or "oauth_state" in response.cookies


@pytest.mark.asyncio
@patch("app.services.github_service.GitHubService.get_primary_email", new_callable=AsyncMock)
@patch("app.services.github_service.GitHubService.get_github_user", new_callable=AsyncMock)
@patch("app.services.github_service.GitHubService.exchange_code_for_token", new_callable=AsyncMock)
async def test_github_oauth_flow(
    mock_exchange, mock_get_user, mock_get_email, async_client: AsyncClient
):
    """Test complete GitHub OAuth flow with valid state and matching cookie.

    The /github/callback endpoint validates:
    1. HMAC-signed state parameter
    2. Cookie-bound state match (CSRF defense)
    3. Nonce single-use (replay defense)
    4. PKCE token exchange
    """
    mock_exchange.return_value = "mock_github_token"
    mock_get_user.return_value = {
        "id": 123456,
        "login": "githubuser",
        "email": "github@example.com",
        "name": "GitHub User",
        "avatar_url": "https://avatars.githubusercontent.com/u/123",
    }
    mock_get_email.return_value = "github@example.com"

    from app.api.v1.auth import _create_oauth_state

    state, nonce = _create_oauth_state()

    response = await async_client.get(
        f"/api/v1/auth/github/callback?code=mock_code&state={state}",
        cookies={"oauth_state": state},
        follow_redirects=False,
    )
    # The callback returns a 302 redirect to the frontend with access_token in the URL fragment
    assert response.status_code == 302
    assert "access_token=" in response.headers["location"]


@pytest.mark.asyncio
async def test_github_oauth_rejects_missing_cookie(async_client: AsyncClient):
    """Test that a callback with a valid signed state but NO cookie is rejected (CSRF protection)."""
    from app.api.v1.auth import _create_oauth_state

    state, nonce = _create_oauth_state()

    response = await async_client.get(
        f"/api/v1/auth/github/callback?code=mock_code&state={state}",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "error=oauth_failed" in response.headers["location"]


@pytest.mark.asyncio
async def test_github_oauth_rejects_mismatched_cookie_csrf_attack(async_client: AsyncClient):
    """
    Simulate login-CSRF attack:
    Attacker captures their own valid state token and tricks victim into visiting callback URL.
    Victim has either no cookie or their own different cookie.
    Must be rejected.
    """
    from app.api.v1.auth import _create_oauth_state

    attacker_state, _ = _create_oauth_state()
    victim_state, _ = _create_oauth_state()

    # Victim visits URL with attacker's state parameter, but victim's browser sends victim's cookie
    response = await async_client.get(
        f"/api/v1/auth/github/callback?code=mock_code&state={attacker_state}",
        cookies={"oauth_state": victim_state},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "error=oauth_failed" in response.headers["location"]


@pytest.mark.asyncio
@patch("app.services.github_service.GitHubService.get_primary_email", new_callable=AsyncMock)
@patch("app.services.github_service.GitHubService.get_github_user", new_callable=AsyncMock)
@patch("app.services.github_service.GitHubService.exchange_code_for_token", new_callable=AsyncMock)
async def test_github_oauth_rejects_replayed_state(
    mock_exchange, mock_get_user, mock_get_email, async_client: AsyncClient
):
    """Test that reusing a previously consumed state nonce is rejected (replay attack prevention)."""
    mock_exchange.return_value = "mock_github_token"
    mock_get_user.return_value = {
        "id": 999123,
        "login": "replayuser",
        "email": "replay@example.com",
        "name": "Replay User",
        "avatar_url": "https://avatars.githubusercontent.com/u/999",
    }
    mock_get_email.return_value = "replay@example.com"

    from app.api.v1.auth import _create_oauth_state

    state, nonce = _create_oauth_state()

    # First attempt: succeeds
    res1 = await async_client.get(
        f"/api/v1/auth/github/callback?code=mock_code&state={state}",
        cookies={"oauth_state": state},
        follow_redirects=False,
    )
    assert res1.status_code == 302
    assert "access_token=" in res1.headers["location"]

    # Second attempt (replay): rejected
    res2 = await async_client.get(
        f"/api/v1/auth/github/callback?code=mock_code&state={state}",
        cookies={"oauth_state": state},
        follow_redirects=False,
    )
    assert res2.status_code == 302
    assert "error=oauth_failed" in res2.headers["location"]


@pytest.mark.asyncio
async def test_github_oauth_rejects_expired_state(async_client: AsyncClient):
    """Test that an HMAC-signed state older than _STATE_MAX_AGE is rejected."""
    import time
    from app.api.v1.auth import _sign

    old_ts = str(int(time.time()) - 1000)  # >600s ago
    nonce = "oldnonce12345678"
    sig = _sign(f"{nonce}.{old_ts}")
    expired_state = f"{nonce}.{old_ts}.{sig}"

    response = await async_client.get(
        f"/api/v1/auth/github/callback?code=mock_code&state={expired_state}",
        cookies={"oauth_state": expired_state},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "error=oauth_failed" in response.headers["location"]


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, test_user_token: str):
    """Test /me endpoint returns user info."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, test_user_token: str):
    """Test logout endpoint clears refresh token."""
    response = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    assert "Logged out" in response.json()["message"]


@pytest.mark.asyncio
async def test_missing_auth_header(async_client: AsyncClient):
    """Test protected endpoint without auth header returns 401.

    HTTPBearer(auto_error=False) yields None when the header is missing,
    and get_current_user raises AuthenticationError (401), not 422.
    """
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_auth_header(async_client: AsyncClient):
    """Test protected endpoint with invalid auth header format."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "InvalidFormat token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sql_injection_in_login(async_client: AsyncClient):
    """Test SQL injection attempt in login is blocked.

    Pydantic's EmailStr validator rejects the malformed email before
    it ever reaches the database layer, returning a 422 validation error.
    This is the correct and safe behavior.
    """
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com'; DROP TABLE users; --",
            "password": "anypassword",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_demo_login_success(async_client: AsyncClient):
    """Test successful demo login."""
    response = await async_client.post("/api/v1/auth/demo")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "demo" in data["user"]["email"]


@pytest.mark.asyncio
async def test_demo_login_exception_hides_traceback_and_returns_generic_error(
    async_client: AsyncClient, caplog
):
    """Test that demo login failure returns only generic error and request_id without traceback leak (F-09)."""
    sensitive_msg = "Database connection postgresql://admin:super_secret_pw@internal.db:5432/devintel failed"
    with patch("app.services.auth_service.AuthService.demo_login", side_effect=RuntimeError(sensitive_msg)):
        response = await async_client.post(
            "/api/v1/auth/demo",
            headers={"X-Request-ID": "test-traceback-req-999"},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "An error occurred processing your request."
        assert data["request_id"] == "test-traceback-req-999"

        # Ensure sensitive info and traceback are NOT leaked to the client
        assert "traceback" not in data
        assert "RuntimeError" not in response.text
        assert "super_secret_pw" not in response.text
        assert "postgresql://" not in response.text

        # Ensure server-side logs recorded the failure and request_id
        assert any(
            record.levelname == "ERROR" and "test-traceback-req-999" in record.message
            for record in caplog.records
        )