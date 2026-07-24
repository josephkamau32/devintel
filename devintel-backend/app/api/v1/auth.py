import secrets
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
    service = AuthService(db)
    user, access_token, refresh_token = await service.demo_login()
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
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
async def github_login(response: Response):
    """Redirect to GitHub for OAuth authorization."""
    state = secrets.token_urlsafe(32)
    # Store the state in a short-lived httponly cookie for validation on callback
    response = RedirectResponse(
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
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=600,  # 10 minutes
    )
    return response


@router.get("/github/callback")
async def github_callback(
    code: str,
    request: Request,
    response: Response,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback with state validation."""
    # Validate OAuth state parameter to prevent CSRF
    stored_state = request.cookies.get("oauth_state")
    if not state or not stored_state or not secrets.compare_digest(state, stored_state):
        raise AuthenticationError("Invalid OAuth state — possible CSRF attack")

    service = GitHubService(db)
    user, access_token, refresh_token = await service.authenticate(code)

    frontend_url = settings.FRONTEND_URL
    redirect = RedirectResponse(
        url=f"{frontend_url}/oauth/callback#access_token={access_token}",
        status_code=302,
    )
    _set_refresh_cookie(redirect, refresh_token)
    # Clear the one-time state cookie
    redirect.delete_cookie("oauth_state")
    return redirect
