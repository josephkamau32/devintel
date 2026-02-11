"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import create_access_token
from app.db.session import get_db
from app.integrations.github_client import GitHubClient, exchange_code_for_token
from app.repositories.user import UserRepository
from app.schemas.user import TokenResponse, UserResponse
from app.api.deps import get_current_user
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/github")
async def github_login():
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
async def github_callback(
    code: str = Query(..., description="OAuth code from GitHub"),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback."""
    try:
        # Exchange code for access token
        access_token = await exchange_code_for_token(code)
        
        # Get user info from GitHub
        github_client = GitHubClient(access_token)
        user_info = await github_client.get_user_info()
        
        # Create or update user
        user_repo = UserRepository(db)
        user = await user_repo.create_or_update_from_github(
            github_id=user_info["github_id"],
            email=user_info.get("email"),
            name=user_info.get("name"),
            avatar_url=user_info.get("avatar_url"),
        )
        
        # Create JWT token
        jwt_token = create_access_token({"sub": str(user.id)})
        
        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
        
    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)
