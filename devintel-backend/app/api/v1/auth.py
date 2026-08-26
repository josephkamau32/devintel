import base64
import hashlib
import hmac
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshResponse,
    SignupRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import AuthService
from app.services.cache import cache
from app.services.github_service import GitHubService

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
COOKIE_SETTINGS = {
    "httponly": True,
    "secure": not settings.DEBUG,
    "samesite": "none" if not settings.DEBUG else "lax",
    "max_age": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
}

# ── HMAC-signed & Cookie-bound OAuth state (CSRF & Replay Protection) ─────
_STATE_MAX_AGE = 600  # 10 minutes
OAUTH_STATE_COOKIE_NAME = "oauth_state"
OAUTH_STATE_COOKIE_SETTINGS = {
    "httponly": True,
    "secure": not settings.DEBUG,
    "samesite": "lax",
    "max_age": _STATE_MAX_AGE,
}


def _sign(payload: str) -> str:
    """Create an HMAC-SHA256 signature of *payload* using SECRET_KEY."""
    return hmac.new(
        settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()[:32]


def _create_oauth_state() -> tuple[str, str]:
    """Build a self-validating state: ``nonce.timestamp.signature`` and return (state, nonce)."""
    nonce = secrets.token_urlsafe(16)
    ts = str(int(time.time()))
    sig = _sign(f"{nonce}.{ts}")
    return f"{nonce}.{ts}.{sig}", nonce


def _extract_oauth_nonce(state: str) -> Optional[str]:
    """Extract nonce from oauth state token."""
    try:
        nonce, ts, sig = state.rsplit(".", 2)
        return nonce
    except ValueError:
        return None


def _verify_oauth_state(state: str) -> bool:
    """Verify the HMAC signature and ensure the state hasn't expired."""
    try:
        nonce, ts, sig = state.rsplit(".", 2)
    except ValueError:
        return False
    expected = _sign(f"{nonce}.{ts}")
    if not hmac.compare_digest(sig, expected):
        return False
    if abs(time.time() - int(ts)) > _STATE_MAX_AGE:
        return False
    return True


def _create_pkce_pair() -> tuple[str, str]:
    """
    Generate PKCE code_verifier and S256 code_challenge (RFC 7636).
    code_verifier: 43-128 unreserved characters
    code_challenge: BASE64URL-ENCODE(SHA256(ASCII(code_verifier))) without padding
    """
    code_verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def _set_oauth_state_cookie(response: Response, state: str) -> None:
    response.set_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        value=state,
        **OAUTH_STATE_COOKIE_SETTINGS,
    )


def _clear_oauth_state_cookie(response: Response) -> None:
    response.delete_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        secure=OAUTH_STATE_COOKIE_SETTINGS["secure"],
        samesite=OAUTH_STATE_COOKIE_SETTINGS["samesite"],
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        **COOKIE_SETTINGS,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        secure=COOKIE_SETTINGS["secure"],
        samesite=COOKIE_SETTINGS["samesite"],
    )


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    data: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, access_token, refresh_token = await service.signup(data)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, access_token, refresh_token = await service.login(data)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


@router.post("/demo", response_model=TokenResponse)
async def demo_login(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """One-click demo login — creates or retrieves a demo user for portfolio demos."""
    request_id = getattr(request.state, "request_id", None) or "unknown"
    try:
        service = AuthService(db)
        user, access_token, refresh_token = await service.demo_login()
        _set_refresh_cookie(response, refresh_token)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserPublic.model_validate(user),
        )
    except Exception as exc:
        logger.error(
            "Demo login failed [request_id=%s]: %s",
            request_id,
            exc,
            exc_info=True,
        )
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An error occurred processing your request.",
                "request_id": request_id,
            },
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise AuthenticationError("No refresh token provided")

    service = AuthService(db)
    new_access, new_refresh = await service.refresh(refresh_token)
    _set_refresh_cookie(response, new_refresh)
    return RefreshResponse(access_token=new_access, token_type="bearer")


@router.post("/logout")
async def logout(response: Response):
    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)


@router.get("/github")
async def github_login():
    """Redirect to GitHub for OAuth authorization with cookie-bound state and PKCE."""
    state, nonce = _create_oauth_state()
    code_verifier, code_challenge = _create_pkce_pair()

    # Store PKCE code_verifier server-side keyed by state nonce
    await cache.set(f"pkce_verifier:{nonce}", code_verifier, ttl=_STATE_MAX_AGE)

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "repo,user:email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    redirect = RedirectResponse(
        url=f"https://github.com/login/oauth/authorize?{urlencode(params)}",
        status_code=302,
    )
    _set_oauth_state_cookie(redirect, state)
    return redirect


@router.get("/github/callback")
async def github_callback(
    code: str,
    request: Request,
    response: Response,
    state: Optional[str] = None,
    oauth_state: Optional[str] = Cookie(None, alias=OAUTH_STATE_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback with state validation, cookie binding, replay protection, and PKCE."""
    frontend_url = settings.FRONTEND_URL

    # 1. State parameter & HMAC signature verification
    if not state or not _verify_oauth_state(state):
        logger.warning(
            "OAuth state HMAC signature/age validation failed — redirecting to login"
        )
        redirect = RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed", status_code=302
        )
        _clear_oauth_state_cookie(redirect)
        return redirect

    # 2. Cookie-binding check (CSRF defense)
    if not oauth_state or not hmac.compare_digest(state, oauth_state):
        logger.warning(
            "OAuth state cookie binding mismatch or missing cookie — possible CSRF attempt"
        )
        redirect = RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed", status_code=302
        )
        _clear_oauth_state_cookie(redirect)
        return redirect

    # 3. Single-use state check (replay protection)
    nonce = _extract_oauth_nonce(state)
    claimed = await cache.setnx(f"oauth_state_used:{nonce}", "1", ttl=_STATE_MAX_AGE)
    if not claimed:
        logger.warning("OAuth state replay detected: nonce=%s", nonce)
        redirect = RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed", status_code=302
        )
        _clear_oauth_state_cookie(redirect)
        return redirect

    # 4. Retrieve PKCE code_verifier
    code_verifier = await cache.get(f"pkce_verifier:{nonce}")

    try:
        service = GitHubService(db)
        user, access_token, refresh_token = await service.authenticate(
            code=code,
            code_verifier=code_verifier,
        )

        redirect = RedirectResponse(
            url=f"{frontend_url}/oauth/callback#access_token={access_token}",
            status_code=302,
        )
        _set_refresh_cookie(redirect, refresh_token)
        _clear_oauth_state_cookie(redirect)
        return redirect

    except Exception as exc:
        logger.error("GitHub OAuth callback failed: %s", exc, exc_info=True)
        redirect = RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed", status_code=302
        )
        _clear_oauth_state_cookie(redirect)
        return redirect
