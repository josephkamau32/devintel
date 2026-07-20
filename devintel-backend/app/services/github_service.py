import logging
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, create_refresh_token, encrypt_token
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_USER_EMAIL_URL = "https://api.github.com/user/emails"


class GitHubService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def exchange_code_for_token(self, code: str) -> str:
        """Exchange GitHub OAuth code for an access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise AuthenticationError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")

        access_token = data.get("access_token")
        if not access_token:
            raise AuthenticationError("GitHub did not return an access token")

        return access_token

    async def get_github_user(self, github_token: str) -> dict:
        """Fetch user profile from GitHub API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_primary_email(self, github_token: str) -> Optional[str]:
        """Fetch the user's primary, verified email from GitHub."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GITHUB_USER_EMAIL_URL,
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10.0,
            )
            if response.status_code != 200:
                return None
            emails = response.json()

        for entry in emails:
            if entry.get("primary") and entry.get("verified"):
                return entry["email"]
        return None

    async def authenticate(self, code: str) -> tuple[User, str, str]:
        """
        Full GitHub OAuth flow:
        1. Exchange code for token
        2. Fetch GitHub profile
        3. Find or create user
        4. Return (user, access_token, refresh_token)
        """
        github_token = await self.exchange_code_for_token(code)
        github_user = await self.get_github_user(github_token)
        email = await self.get_primary_email(github_token)

        github_id = str(github_user["id"])
        encrypted_token = encrypt_token(github_token)

        user = await self.user_repo.get_by_github_id(github_id)

        if user:
            user = await self.user_repo.update_github_token(user, encrypted_token)
            logger.info("Existing GitHub user logged in: id=%s", user.id)
        else:
            if email:
                existing = await self.user_repo.get_by_email(email)
                if existing:
                    user = await self.user_repo.link_github_account(
                        user=existing,
                        github_id=github_id,
                        github_username=github_user.get("login"),
                        encrypted_token=encrypted_token,
                        avatar_url=github_user.get("avatar_url"),
                    )
                    logger.info("Linked GitHub to existing email user: id=%s", user.id)

            if not user:
                user = await self.user_repo.create_github_user(
                    github_id=github_id,
                    github_username=github_user.get("login", ""),
                    github_token_encrypted=encrypted_token,
                    email=email,
                    full_name=github_user.get("name"),
                    avatar_url=github_user.get("avatar_url"),
                )
                logger.info("New GitHub user created: id=%s", user.id)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token
