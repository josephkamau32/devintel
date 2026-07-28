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
from app.services.github_service import GitHubService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
COOKIE_SETTINGS = {
    "httponly": True,
    "secure": not settings.DEBUG,
    "samesite": "none" if not settings.DEBUG else "lax",
    "max_age": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
}

# ── HMAC-signed OAuth state (stateless CSRF protection) ───────────────────
_STATE_MAX_AGE = 600  # 10 minutes


def _sign(payload: str) -> str:
    """Create an HMAC-SHA256 signature of *payload* using SECRET_KEY."""
    return hmac.new(
        settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()[:32]


def _create_oauth_state() -> str:
    """Build a self-validating state: ``nonce.timestamp.signature``."""
    nonce = secrets.token_urlsafe(16)
    ts = str(int(time.time()))
    sig = _sign(f"{nonce}.{ts}")
    return f"{nonce}.{ts}.{sig}"


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
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """One-click demo login — creates or retrieves a demo user for portfolio demos."""
    import logging as _logging
    import traceback
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
        tb = traceback.format_exc()
        _logging.getLogger(__name__).error("Demo login failed:\n%s", tb)
        # Surface the real error so we can debug without Render log access
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Demo login error: {type(exc).__name__}: {exc}",
                "traceback": tb.split("\n")[-5:],
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
    """Redirect to GitHub for OAuth authorization."""
    # Use an HMAC-signed state token instead of a cookie.
    # Cookies are unreliable across the multi-hop redirect chain
    # (backend → GitHub → backend) due to SameSite restrictions.
    state = _create_oauth_state()
    return RedirectResponse(
        url="https://github.com/login/oauth/authorize?"
        + urlencode(
            {
                "client_id": settings.GITHUB_CLIENT_ID,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
                "scope": "repo,user:email",
                "state": state,
            }
        )
    )


@router.get("/github/callback")
async def github_callback(
    code: str,
    request: Request,
    response: Response,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback with state validation."""
    import logging as _logging
    import traceback

    frontend_url = settings.FRONTEND_URL

    # Validate the HMAC-signed state token (no cookie needed)
    if not state or not _verify_oauth_state(state):
        _logging.getLogger(__name__).warning(
            "OAuth state validation failed — redirecting to login"
        )
        return RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed", status_code=302
        )

    try:
        service = GitHubService(db)
        user, access_token, refresh_token = await service.authenticate(code)

        redirect = RedirectResponse(
            url=f"{frontend_url}/oauth/callback#access_token={access_token}",
            status_code=302,
        )
        _set_refresh_cookie(redirect, refresh_token)
        return redirect

    except Exception as exc:
        _logging.getLogger(__name__).error(
            "GitHub OAuth callback failed: %s\n%s",
            exc,
            traceback.format_exc(),
        )
        # Redirect to frontend login with error — never show a raw error page
        return RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed", status_code=302
        )
