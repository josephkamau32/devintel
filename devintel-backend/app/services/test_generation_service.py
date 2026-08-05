"""Test generation service for autonomous PR workflow."""

from typing import Any
from uuid import UUID

from app.core.exceptions import APIError
from app.core.logging import get_logger
from app.ai.orchestrator import get_orchestrator
from app.models.generated_test import TestStatus
from app.models.repository import Repository
from app.repositories.generated_test import GeneratedTestRepository
from app.services.sandbox_service import SandboxService

logger = get_logger(__name__)


class TestGenerationService:
    """Generate and execute tests for code changes."""

    def __init__(self, db_session):
        self.db = db_session
        self.orchestrator = get_orchestrator()

    async def generate_and_run_tests(
        self,
        repo: Repository,
        file_changes: list[dict[str, str]],
        repo_id: UUID,
    ) -> dict[str, Any]:
        """
        Generate tests for changed files and run them.

        Args:
            repo: Repository object
            file_changes: List of {path, content} dicts
            repo_id: Repository UUID

        Returns:
            Dict with test results summary
        """
        test_repo = GeneratedTestRepository(self.db)

        # Prepare context for LLM
        context = self._build_test_context(file_changes)

        # Generate test code
        system_prompt = f"""You are a test engineer. Generate pytest unit tests for the following code changes.

Repository: {repo.full_name}
Language: {repo.language or 'unknown'}

Context:
{context}

Return only valid Python test code with appropriate imports. Ensure tests cover:
- Happy path scenarios
- Edge cases
- Error handling
- Main functionality paths
"""

        try:
            response = await self.orchestrator.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate comprehensive unit tests for the modified code."}
                ],
                temperature=0.2,
                max_tokens=3000,
                agent="test_generation",
            )

            test_content = response.content

            # Create test record
            test_record = await test_repo.create(
                repo_id=repo_id,
                file_path=f"test_{file_changes[0]['path'].replace('/', '_').replace('.py', '_test.py')}" if file_changes else "test_generated.py",
                test_content=test_content,
                status=TestStatus.PENDING,
            )

            # Prepare patched files for sandbox
            patched_files = {fc["path"]: fc["content"] for fc in file_changes}

            # Run tests in sandbox
            await test_repo.update(test_record.id, status=TestStatus.RUNNING)
            await self.db.commit()

            result = await SandboxService.run_tests(
                test_content=test_content,
                patched_files=patched_files,
                test_file_path=test_record.file_path,
            )

            # Update test record with results
            await test_repo.update(
                test_record.id,
                status=TestStatus.PASSED if result["passed"] else TestStatus.FAILED,
                output=result.get("output", ""),
            )
            await self.db.commit()

            return {
                "test_id": str(test_record.id),
                "passed": result["passed"],
                "output": result.get("output", ""),
            }

        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            raise APIError(f"Test generation failed: {str(e)}") from e

    def _build_test_context(self, file_changes: list[dict[str, str]]) -> str:
        """Build context string for test generation prompt."""
        context = ""
        for fc in file_changes[:3]:  # Limit to 3 files for context
            context += f"\n\n--- File: {fc['path']} ---\n"
            context += fc["content"][:1500]  # Truncate for context
        return context
