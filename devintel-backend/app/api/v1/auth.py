"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.constants import AUTH_RATE_LIMIT
from app.db.session import get_db
from app.integrations.github_client import GitHubClient, exchange_code_for_token
from app.repositories.user import UserRepository
from app.schemas.user import TokenResponse, UserResponse, RefreshTokenRequest, UserUpdate
from app.api.deps import get_current_user
from app.models.user import User
from app.services.encryption import encryption_service

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/github")
@limiter.limit(AUTH_RATE_LIMIT)
async def github_login(request: Request):
    """Redirect to GitHub OAuth."""
    from app.core.config import settings
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=read:user,user:email,repo"
    )
    
    return {"url": github_auth_url}


@router.get("/github/callback", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def github_callback(
    request: Request,
    code: str = Query(..., description="OAuth code from GitHub"),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback."""
    try:
        # Exchange code for access token
        github_access_token = await exchange_code_for_token(code)
        
        # Get user info from GitHub
        github_client = GitHubClient(github_access_token)
        user_info = await github_client.get_user_info()
        
        # Encrypt GitHub token for storage
        encrypted_token = encryption_service.encrypt(github_access_token)
        
        # Create or update user with encrypted token
        user_repo = UserRepository(db)
        user = await user_repo.create_or_update_from_github(
            github_id=user_info["github_id"],
            email=user_info.get("email"),
            name=user_info.get("name"),
            username=user_info.get("login"),
            avatar_url=user_info.get("avatar_url"),
            github_token_encrypted=encrypted_token,
        )
        
        # Create JWT tokens
        jwt_access_token = create_access_token({"sub": str(user.id)})
        jwt_refresh_token = create_refresh_token({"sub": str(user.id)})
        
        # Store refresh token
        user.refresh_token = jwt_refresh_token
        await db.commit()
        
        return TokenResponse(
            access_token=jwt_access_token,
            refresh_token=jwt_refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
        
    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def refresh_access_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = verify_token(refresh_request.refresh_token)
        
        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        # Verify refresh token matches stored token
        user_repo = UserRepository(db)
        from uuid import UUID
        user = await user_repo.get_by_id(UUID(user_id))
        
        if not user or user.refresh_token != refresh_request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Create new access token
        new_access_token = create_access_token({"sub": str(user.id)})
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_request.refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    user_repo = UserRepository(db)
    
    # Filter out None values
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    if not update_data:
        return UserResponse.model_validate(current_user)
        
    updated_user = await user_repo.update(current_user.id, **update_data)
    return UserResponse.model_validate(updated_user)
