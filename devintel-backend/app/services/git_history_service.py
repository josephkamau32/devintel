"""Git history service for indexing and blame analysis."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.integrations.github_client import GitHubClient
from app.models.git_history import GitHistory, FileBlame
from app.models.repository import Repository
from app.repositories.git_history import GitHistoryRepository, FileBlameRepository

logger = get_logger(__name__)


class GitHistoryService:
    """Service for git history indexing and blame analysis."""

    def __init__(self, db_session, github_token: Optional[str] = None):
        self.db = db_session
        self.github_client = GitHubClient(github_token) if github_token else None

    async def index_repository_history(
        self,
        repository: Repository,
        github_token: Optional[str] = None,
        max_commits: int = 500,
    ) -> dict:
        """
        Index git commit history for a repository.

        Args:
            repository: Repository to index
            github_token: GitHub token for API calls
            max_commits: Maximum commits to index

        Returns:
            Dict with indexing stats
        """
        client = self.github_client or GitHubClient(github_token) if github_token else None
        if not client:
            raise ValueError("GitHub token required for history indexing")

        git_repo = GitHistoryRepository(self.db)
        indexed = 0
        last_sha = None

        try:
            # Get commit history
            commits = await client.get_commits(
                full_name=repository.full_name,
                per_page=min(max_commits, 100),
            )

            for commit in commits:
                # Check if already indexed
                existing = await git_repo.get_by_repo_and_sha(repository.id, commit["sha"])
                if existing:
                    last_sha = commit["sha"]
                    continue

                # Create record
                await git_repo.create(
                    repo_id=repository.id,
                    sha=commit["sha"],
                    message=commit.get("commit", {}).get("message", ""),
                    author_name=commit.get("commit", {}).get("author", {}).get("name", ""),
                    author_email=commit.get("commit", {}).get("author", {}).get("email", ""),
                    committed_at=datetime.fromisoformat(
                        commit.get("commit", {}).get("author", {}).get("date", "").replace("Z", "+00:00")
                    ) if commit.get("commit", {}).get("author", {}).get("date") else None,
                    files_changed=commit.get("files_changed", 0),
                    additions=commit.get("additions", 0),
                    deletions=commit.get("deletions", 0),
                    changed_files=commit.get("files", []),
                )
                indexed += 1
                last_sha = commit["sha"]

            await self.db.commit()

            return {
                "indexed_commits": indexed,
                "last_sha": last_sha,
            }

        except Exception as e:
            logger.error(f"Failed to index git history for {repository.full_name}: {e}")
            await self.db.rollback()
            raise

    async def get_blame_for_file(
        self,
        repository: Repository,
        file_path: str,
        ref: str = "main",
    ) -> list[FileBlame]:
        """
        Get blame information for a file.

        Args:
            repository: Repository
            file_path: Path to file
            ref: Git reference (branch/tag/sha)

        Returns:
            List of FileBlame records
        """
        blame_repo = FileBlameRepository(self.db)

        # Check cache first
        cached = await blame_repo.get_by_repo_and_file(repository.id, file_path, limit=1000)
        if cached:
            return cached

        if not self.github_client:
            raise ValueError("GitHub client required for blame")

        try:
            # Get blame from GitHub API
            blame_data = await self.github_client.get_file_blame(
                full_name=repository.full_name,
                file_path=file_path,
                ref=ref,
            )

            blame_records = []
            for entry in blame_data:
                record = await blame_repo.create(
                    repo_id=repository.id,
                    file_path=file_path,
                    line_number=entry.get("line_number", 0),
                    line_content=entry.get("line_content", ""),
                    commit_sha=entry.get("sha", "")[:40],
                    commit_message=entry.get("commit_message", ""),
                    author_name=entry.get("author_name", ""),
                    commit_date=datetime.fromisoformat(entry.get("date", "").replace("Z", "+00:00")) if entry.get("date") else None,
                )
                blame_records.append(record)

            await self.db.commit()
            return blame_records

        except Exception as e:
            logger.error(f"Failed to get blame for {file_path}: {e}")
            raise

    async def get_recent_commits(
        self,
        repository: Repository,
        limit: int = 50,
    ) -> list[GitHistory]:
        """Get recent commits for a repository."""
        git_repo = GitHistoryRepository(self.db)
        return await git_repo.get_by_repo(repository.id, limit=limit)

    async def get_changes_for_line(
        self,
        repository: Repository,
        file_path: str,
        line_number: int,
    ) -> dict:
        """
        Get git history context for a specific line.

        Returns the commit that introduced this line and subsequent changes.
        """
        blame_repo = FileBlameRepository(self.db)
        blame_entry = await blame_repo.get_by_repo_file_line(
            repository.id, file_path, line_number
        )

        if not blame_entry:
            return {}

        git_repo = GitHistoryRepository(self.db)
        commit = await git_repo.get_by_repo_and_sha(
            repository.id, blame_entry.commit_sha
        )

        return {
            "line_number": line_number,
            "commit_sha": blame_entry.commit_sha,
            "commit_message": blame_entry.commit_message,
            "author": blame_entry.author_name,
            "introduced_at": blame_entry.commit_date,
            "commit_data": {
                "sha": commit.sha if commit else None,
                "message": commit.message if commit else None,
                "committed_at": commit.committed_at if commit else None,
            } if commit else None,
        }