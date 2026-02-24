"""GitHub API client."""

from typing import Any, Dict, List, Optional

import httpx
from github import Github, GithubException

from app.core.config import settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class GitHubClient:
    """GitHub API client wrapper."""

    def __init__(self, access_token: str):
        """Initialize GitHub client."""
        self.client = Github(access_token)
        self.access_token = access_token

    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        try:
            user = self.client.get_user()
            return {
                "github_id": str(user.id),
                "login": user.login,
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
            }
        except GithubException as e:
            logger.error(f"Failed to get user info: {e}")
            raise ExternalServiceError(
                message="Failed to fetch GitHub user info",
                details={"error": str(e)},
            )

    async def get_user_repositories(
        self,
        page: int = 1,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get user repositories."""
        try:
            user = self.client.get_user()
            repos = user.get_repos(
                type="all",
                sort="updated",
                direction="desc",
            )
            
            # Paginate
            start = (page - 1) * per_page
            end = start + per_page
            
            repos_data = []
            for repo in list(repos)[start:end]:
                repos_data.append({
                    "repo_name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "stars": repo.stargazers_count,
                    "language": repo.language,
                    "private": repo.private,
                })
            
            return repos_data
            
        except GithubException as e:
            logger.error(f"Failed to get repositories: {e}")
            raise ExternalServiceError(
                message="Failed to fetch GitHub repositories",
                details={"error": str(e)},
            )

    async def get_repository_pull_requests(
        self,
        full_name: str,
        state: str = "open",
        page: int = 1,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get pull requests for a specific repository."""
        try:
            repo = self.client.get_repo(full_name)
            pulls = repo.get_pulls(
                state=state,
                sort="created",
                direction="desc",
            )
            
            # Paginate
            start = (page - 1) * per_page
            end = start + per_page
            
            pulls_data = []
            for pr in list(pulls)[start:end]:
                pulls_data.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "author": pr.user.login,
                    "author_avatar": pr.user.avatar_url,
                    "created_at": pr.created_at.isoformat(),
                    "updated_at": pr.updated_at.isoformat(),
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "url": pr.html_url,
                })
            
            return pulls_data
            
        except GithubException as e:
            logger.error(f"Failed to get pull requests for {full_name}: {e}")
            raise ExternalServiceError(
                message=f"Failed to fetch pull requests from GitHub",
                details={"error": str(e)},
            )

    async def get_pull_request_diff(self, full_name: str, pr_number: int) -> str:
        """Get the diff for a pull request."""
        try:
            repo = self.client.get_repo(full_name)
            pr = repo.get_pull(pr_number)
            
            # Use raw patch/diff via httpx for cleaner handling if needed,
            # but PyGithub provides get_files() which we could use, 
            # however a single diff string is what our current API expects.
            # PyGithub's pr.diff_url provides the raw diff.
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    pr.diff_url,
                    headers={"Authorization": f"token {self.access_token}"}
                )
                if response.status_code != 200:
                    raise ExternalServiceError(
                        message="Failed to fetch PR diff from GitHub",
                        details={"status_code": response.status_code}
                    )
                return response.text
                
        except (GithubException, httpx.HTTPError) as e:
            logger.error(f"Failed to get diff for PR #{pr_number} in {full_name}: {e}")
            raise ExternalServiceError(
                message=f"Failed to fetch PR diff from GitHub",
                details={"error": str(e)},
            )

    def close(self) -> None:
        """Close client connections."""
        pass


async def exchange_code_for_token(code: str) -> str:
    """Exchange OAuth code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
        )
        
        if response.status_code != 200:
            raise ExternalServiceError(
                message="Failed to exchange GitHub OAuth code",
                details={"status_code": response.status_code},
            )
        
        data = response.json()
        
        if "access_token" not in data:
            raise ExternalServiceError(
                message="No access token in GitHub response",
                details=data,
            )
        
        return data["access_token"]
