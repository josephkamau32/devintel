"""Tests for app.middleware.csrf — CSRF protection middleware security enforcement."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, Request, Response

from app.middleware.csrf import CSRFMiddleware


@pytest.fixture
def middleware():
    # Pass a dummy app to base middleware
    dummy_app = MagicMock()
    return CSRFMiddleware(dummy_app, secret_key="test-secret-key-1234")


def make_request(
    method: str = "POST",
    path: str = "/profile/update",
    cookies: dict | None = None,
    headers: dict | None = None,
) -> Request:
    """Create a mock Request with specified method, path, cookies, and headers."""
    req = MagicMock(spec=Request)
    req.method = method
    req.url = MagicMock()
    req.url.path = path
    req.cookies = cookies or {}
    req.headers = headers or {}
    req.state = MagicMock()
    # Ensure request.state does NOT have csrf_token initially
    del req.state.csrf_token
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    return req


class TestCSRFMiddleware:
    @pytest.mark.asyncio
    async def test_safe_get_request_calls_next_and_sets_cookie(self, middleware):
        req = make_request(method="GET", path="/profile")
        mock_response = Response(content="ok", status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        resp = await middleware.dispatch(req, call_next)
        assert resp.status_code == 200
        call_next.assert_called_once_with(req)
        # Check cookie was added to response headers
        set_cookie_header = resp.headers.get("set-cookie", "")
        assert "csrf_token=" in set_cookie_header

    @pytest.mark.asyncio
    async def test_head_and_options_are_exempt_safe_methods(self, middleware):
        for safe_method in ["HEAD", "OPTIONS"]:
            req = make_request(method=safe_method, path="/anything")
            mock_response = Response(status_code=200)
            call_next = AsyncMock(return_value=mock_response)

            resp = await middleware.dispatch(req, call_next)
            assert resp.status_code == 200
            call_next.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_post_without_tokens_raises_403_missing(self, middleware):
        req = make_request(method="POST", path="/profile/update")
        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(req, call_next)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "CSRF token missing"
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_put_without_tokens_raises_403(self, middleware):
        req = make_request(method="PUT", path="/settings")
        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(req, call_next)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "CSRF token missing"

    @pytest.mark.asyncio
    async def test_delete_without_tokens_raises_403(self, middleware):
        req = make_request(method="DELETE", path="/items/1")
        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(req, call_next)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "CSRF token missing"

    @pytest.mark.asyncio
    async def test_post_with_cookie_only_raises_403_missing(self, middleware):
        req = make_request(
            method="POST",
            path="/profile/update",
            cookies={"csrf_token": "token-123"},
            headers={},  # Missing X-CSRF-Token header
        )
        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(req, call_next)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "CSRF token missing"

    @pytest.mark.asyncio
    async def test_post_with_header_only_raises_403_missing(self, middleware):
        req = make_request(
            method="POST",
            path="/profile/update",
            cookies={},  # Missing csrf_token cookie
            headers={"X-CSRF-Token": "token-123"},
        )
        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(req, call_next)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "CSRF token missing"

    @pytest.mark.asyncio
    async def test_post_with_mismatched_tokens_raises_403_invalid(self, middleware):
        req = make_request(
            method="POST",
            path="/profile/update",
            cookies={"csrf_token": "correct-token"},
            headers={"X-CSRF-Token": "tampered-token"},
        )
        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(req, call_next)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "CSRF token invalid"
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_post_with_matching_tokens_succeeds(self, middleware):
        valid_token = "secure-random-token-xyz"
        req = make_request(
            method="POST",
            path="/profile/update",
            cookies={"csrf_token": valid_token},
            headers={"X-CSRF-Token": valid_token},
        )
        mock_response = Response(content="success", status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        resp = await middleware.dispatch(req, call_next)
        assert resp.status_code == 200
        call_next.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_exempt_prefix_api_v1_allowed_without_tokens(self, middleware):
        req = make_request(method="POST", path="/api/v1/auth/login")
        mock_response = Response(content="logged_in", status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        resp = await middleware.dispatch(req, call_next)
        assert resp.status_code == 200
        call_next.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_exempt_exact_paths_allowed_without_tokens(self, middleware):
        for path in ["/docs", "/redoc", "/openapi.json", "/api/v1/auth/github"]:
            req = make_request(method="POST", path=path)
            mock_response = Response(status_code=200)
            call_next = AsyncMock(return_value=mock_response)

            resp = await middleware.dispatch(req, call_next)
            assert resp.status_code == 200
            call_next.assert_called_once_with(req)

    def test_generate_csrf_token_length_and_randomness(self, middleware):
        token1 = middleware._generate_csrf_token()
        token2 = middleware._generate_csrf_token()
        assert len(token1) >= 32
        assert token1 != token2
