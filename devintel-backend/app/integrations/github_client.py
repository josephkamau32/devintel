"""GitHub API client."""

import asyncio
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
        self.client = Github(access_token, per_page=30)
        self.access_token = access_token

    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        try:
            user = await asyncio.to_thread(self.client.get_user)
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
        """Get user repositories with true pagination."""
        try:
            def _fetch_repos_page():
                user = self.client.get_user()
                repos = user.get_repos(type="all", sort="updated", direction="desc")
                # Use PyGithub's native pagination — O(1) API call per page
                page_data = repos.get_page(page - 1)  # PyGithub pages are 0-indexed
                return [
                    {
                        "repo_name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "url": repo.html_url,
                        "clone_url": repo.clone_url,
                        "stars": repo.stargazers_count,
                        "language": repo.language,
                        "private": repo.private,
                    }
                    for repo in page_data[:per_page]
                ]

            return await asyncio.to_thread(_fetch_repos_page)

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
        """Get pull requests for a specific repository with true pagination."""
        try:
            def _fetch_pulls_page():
                repo = self.client.get_repo(full_name)
                pulls = repo.get_pulls(state=state, sort="created", direction="desc")
                page_data = pulls.get_page(page - 1)
                return [
                    {
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
                    }
                    for pr in page_data[:per_page]
                ]

            return await asyncio.to_thread(_fetch_pulls_page)

        except GithubException as e:
            logger.error(f"Failed to get pull requests for {full_name}: {e}")
            raise ExternalServiceError(
                message=f"Failed to fetch pull requests from GitHub",
                details={"error": str(e)},
            )

    async def get_pull_request_diff(self, full_name: str, pr_number: int) -> str:
        """Get the diff for a pull request."""
        try:
            # Offload sync PyGithub calls to thread
            def _get_pr_diff_url():
                repo = self.client.get_repo(full_name)
                pr = repo.get_pull(pr_number)
                return pr.diff_url

            diff_url = await asyncio.to_thread(_get_pr_diff_url)

            # Async HTTP fetch for the diff content
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    diff_url,
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

    async def create_branch(self, full_name: str, base_branch: str, new_branch_name: str) -> str:
        """Create a new branch from a base branch."""
        try:
            def _do_create_branch():
                repo = self.client.get_repo(full_name)
                # Ensure refs/heads/ prefix
                new_ref = f"refs/heads/{new_branch_name}" if not new_branch_name.startswith("refs/") else new_branch_name
                # Get the base branch SHA
                base_ref = repo.get_branch(base_branch)
                # Create the branch
                repo.create_git_ref(ref=new_ref, sha=base_ref.commit.sha)
                return new_branch_name

            return await asyncio.to_thread(_do_create_branch)
        except GithubException as e:
            logger.error(f"Failed to create branch {new_branch_name} in {full_name}: {e}")
            raise ExternalServiceError(
                message=f"Failed to create branch on GitHub",
                details={"error": str(e)},
            )

    async def create_commit(
        self,
        full_name: str,
        branch_name: str,
        file_changes: List[Dict[str, str]],
        commit_message: str,
    ) -> str:
        """
        Create a multi-file commit using the Git Data API.
        file_changes: [{"path": "src/main.py", "content": "print('hello')"}]
        """
        try:
            def _do_create_commit():
                repo = self.client.get_repo(full_name)
                
                # Get the branch reference
                ref = repo.get_git_ref(f"heads/{branch_name}")
                base_commit = repo.get_git_commit(ref.object.sha)
                base_tree = repo.get_git_tree(base_commit.tree.sha)
                
                # Create blobs and build tree elements
                element_list = []
                for change in file_changes:
                    # Note: We are using "100644" for file mode, and "blob" for type
                    blob = repo.create_git_blob(change["content"], "utf-8")
                    from github.InputGitTreeElement import InputGitTreeElement
                    element = InputGitTreeElement(
                        path=change["path"],
                        mode='100644',
                        type='blob',
                        sha=blob.sha
                    )
                    element_list.append(element)
                
                # Create the new tree
                new_tree = repo.create_git_tree(element_list, base_tree)
                
                # Create the commit
                new_commit = repo.create_git_commit(
                    commit_message,
                    new_tree,
                    [base_commit]
                )
                
                # Update the branch reference
                ref.edit(new_commit.sha)
                
                return new_commit.sha

            return await asyncio.to_thread(_do_create_commit)
        except GithubException as e:
            logger.error(f"Failed to create commit on branch {branch_name} in {full_name}: {e}")
            raise ExternalServiceError(
                message=f"Failed to commit files to GitHub",
                details={"error": str(e)},
            )

    async def create_pull_request(
        self,
        full_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
    ) -> Dict[str, Any]:
        """Create a new Pull Request."""
        try:
            def _do_create_pr():
                repo = self.client.get_repo(full_name)
                pr = repo.create_pull(
                    title=title,
                    body=body,
                    head=head_branch,
                    base=base_branch,
                )
                return {
                    "number": pr.number,
                    "url": pr.html_url,
                    "title": pr.title,
                }

            return await asyncio.to_thread(_do_create_pr)
        except GithubException as e:
            logger.error(f"Failed to create pull request in {full_name}: {e}")
            raise ExternalServiceError(
                message=f"Failed to create Pull Request on GitHub",
                details={"error": str(e)},
            )


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
                # Must match the redirect_uri used in the authorization URL
                "redirect_uri": settings.github_redirect_uri,
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
