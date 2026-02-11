"""API dependencies."""

from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get current authenticated user."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise AuthenticationError("User not found")
        
        return user
        
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
