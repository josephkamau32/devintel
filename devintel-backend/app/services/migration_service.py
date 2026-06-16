"""Code migration service for AI-powered migration."""

from typing import Any, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient
from app.models.migration import MigrationProject, MigratedFile
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.migration import MigrationProjectRepository, MigratedFileRepository
from app.services.retrieval.hybrid_retriever import HybridRetriever

logger = get_logger(__name__)


class CodeMigrationService:
    """Service for AI-powered code migration between technologies."""

    def __init__(self, db_session):
        self.db = db_session
        self.openai_client = OpenAIClient()

    async def create_migration_project(
        self,
        repository: Repository,
        source_tech: str,
        target_tech: str,
    ) -> MigrationProject:
        """
        Create a new migration project.

        Args:
            repository: Repository to migrate
            source_tech: Source technology (e.g., "javascript", "python2")
            target_tech: Target technology (e.g., "typescript", "python3")

        Returns:
            MigrationProject instance
        """
        project_repo = MigrationProjectRepository(self.db)

        # Count Python files for initial estimate
        file_count = await self._count_files(repository)

        project = await project_repo.create(
            repo_id=repository.id,
            source_tech=source_tech,
            target_tech=target_tech,
            status="pending",
            progress_percent=0,
            total_files=file_count,
        )
        await self.db.commit()

        return project

    async def generate_migration_plan(
        self,
        project: MigrationProject,
        repo: Repository,
    ) -> str:
        """Generate migration plan using LLM."""
        retriever = HybridRetriever(EmbeddingRepository(self.db))
        code_files = await retriever.search(
            repo.id,
            f"{project.source_tech} code files",
            top_k=20,
        )

        context = "".join(
            f"\n--- {emb.file_path} ---\n{emb.chunk_text[:500]}"
            for emb, _ in code_files[:10]
        )

        system_prompt = f"""You are DevIntel Migration Agent. Migrate code from {project.source_tech} to {project.target_tech}.

Context from codebase:
{context}

Generate a migration plan including:
1. Key transformations needed
2. Breaking changes to watch for
3. Recommended migration strategy
4. File-by-file migration approach"""

        response = await self.openai_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate a detailed migration plan."}
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        plan = response.content if hasattr(response, "content") else str(response)

        await MigrationProjectRepository(self.db).update(project.id, migration_plan=plan)
        return plan

    async def migrate_file(
        self,
        project: MigrationProject,
        file_path: str,
        file_content: str,
    ) -> MigratedFile:
        """Migrate a single file."""
        migrated_repo = MigratedFileRepository(self.db)

        # Get migration plan context
        prompt = f"""Migrate this {project.source_tech} code to {project.target_tech}:

```
{file_content[:3000]}
```

Provide the fully migrated code for {project.target_tech}."""

        response = await self.openai_client.chat_completion(
            messages=[
                {"role": "system", "content": f"You are a migration expert converting {project.source_tech} to {project.target_tech}."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000,
        )

        migrated_content = response.content if hasattr(response, "content") else str(response)

        # Create migrated file record
        migrated_file = await migrated_repo.create(
            project_id=project.id,
            original_path=file_path,
            migrated_path=file_path.replace(f".{project.source_tech}", f".{project.target_tech}") if "." in project.source_tech else f"{file_path}.{project.target_tech}",
            content=migrated_content,
            status="completed",
        )
        await self.db.commit()

        return migrated_file

    async def _count_files(self, repository: Repository) -> int:
        """Count files for migration estimate."""
        from app.repositories.embedding import EmbeddingRepository
        emb_repo = EmbeddingRepository(self.db)
        files = await emb_repo.get_distinct_file_paths(repository.id)
        return len(files) if files else 0


# Add get_distinct_file_paths method to EmbeddingRepository
def get_distinct_file_paths(self, repo_id: UUID) -> list[str]:
    """Get distinct file paths for a repository."""
    from sqlalchemy import select, distinct
    result = self.db.execute(
        select(distinct(self.model.file_path)).where(self.model.repo_id == repo_id)
    )
    return [r[0] for r in result.fetchall()]


# Monkey-patch the method
MigrationProjectRepository._count_files_orig = MigrationProjectRepository._count_files if hasattr(MigrationProjectRepository, '_count_files') else None