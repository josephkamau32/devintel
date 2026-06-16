"""Agent service for autonomous actions."""

import json
from typing import Any

from app.core.logging import get_logger
from app.integrations.github_client import GitHubClient
from app.integrations.openai_client import OpenAIClient
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.chat import ChatService

logger = get_logger(__name__)


class AgentService:
    """Service for executing autonomous actions via LLMs and GitHub API."""

    def __init__(self, github_token: str):
        """Initialize service."""
        self.openai_client = OpenAIClient()
        self.github_client = GitHubClient(github_token)
        self.chat_service = ChatService()

    @property
    def create_pr_tool(self) -> dict[str, Any]:
        """Tool definition for creating a pull request."""
        return {
            "type": "function",
            "function": {
                "name": "create_pull_request",
                "description": "Create a Pull Request that implements the user's requested code changes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "branch_name": {
                            "type": "string",
                            "description": "A short, descriptive snake_case name for the new branch (e.g., feature/add_login_button, fix/resolve_null_pointer). Do NOT include refs/heads."
                        },
                        "pr_title": {
                            "type": "string",
                            "description": "Clear and concise title for the Pull Request."
                        },
                        "pr_body": {
                            "type": "string",
                            "description": "Detailed markdown description of the changes made, why they were made, and any context."
                        },
                        "commit_message": {
                            "type": "string",
                            "description": "The commit message for the changes."
                        },
                        "file_changes": {
                            "type": "array",
                            "description": "List of files to create or modify. You must provide the FULL updated content of the file, not just snippets.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {
                                        "type": "string",
                                        "description": "The absolute or relative path to the file in the repository (e.g., src/components/Button.tsx)."
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The EXACT, FULL, and COMPLETE new content of the file. Do not truncate or use placeholders."
                                    }
                                },
                                "required": ["path", "content"]
                            }
                        }
                    },
                    "required": ["branch_name", "pr_title", "pr_body", "commit_message", "file_changes"]
                }
            }
        }

    async def draft_pr_plan(
        self,
        repository: Repository,
        instruction: str,
        embedding_repo: EmbeddingRepository,
    ) -> dict[str, Any]:
        """
        Drafts a Pull Request plan by retrieving context and prompting the LLM.
        Does not execute any changes on GitHub.
        """
        repo_name = repository.full_name

        # 1. Retrieve Context
        logger.info(f"Retrieving context for agent draft on {repo_name}...")
        context_chunks = await self.chat_service.retrieve_relevant_chunks(
            repo_id=repository.id,
            question=instruction,
            embedding_repo=embedding_repo,
            top_k=8,  # Agents generally need a bit more context
        )

        # 2. Build Agent Prompt
        context_text = ""
        for embedding, _ in context_chunks:
            context_text += f"\n\n--- File: {embedding.file_path} ---\n{embedding.chunk_text}\n"

        system_prompt = f"""You are DevIntel Agent, an elite autonomous software engineer working on the repository: {repo_name}.

Context from the codebase:
{context_text}

Your task is to implement the user's instructions by writing production-grade code.
You MUST use the `create_pull_request` tool to submit your work.
When using the tool, you must provide the ENTIRE updated content for each file you modify. DO NOT leave placeholders like "// ... rest of code".
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
        ]

        # 3. Call OpenAI with forced tool choice
        logger.info(f"Calling LLM for agent draft on {repo_name}...")
        response_message = await self.openai_client.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
            tools=[self.create_pr_tool],
            tool_choice={"type": "function", "function": {"name": "create_pull_request"}},
        )

        # Ensure we got a tool call
        if not hasattr(response_message, "tool_calls") or not response_message.tool_calls:
            raise ValueError("The AI failed to generate a Pull Request instruction. Please try making your request more specific.")

        tool_call = response_message.tool_calls[0]
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM tool call arguments: {e}")
            raise ValueError("The AI generated an invalid code payload. Please try again.")

        if not args.get("file_changes"):
            raise ValueError("The AI did not suggest any file changes for this request.")

        return args

    async def execute_pr(
        self,
        repository: Repository,
        draft_payload: dict[str, Any],
        default_branch: str = "main",
    ) -> dict[str, Any]:
        """
        Executes a drafted Pull Request plan on GitHub.
        Includes optional test generation and verification.
        """
        repo_name = repository.full_name

        branch_name = draft_payload["branch_name"]
        pr_title = draft_payload["pr_title"]
        pr_body = draft_payload["pr_body"]
        commit_message = draft_payload["commit_message"]
        file_changes = draft_payload["file_changes"]

        # Optional: Generate and run tests before committing
        if draft_payload.get("generate_tests", False):
            from app.services.test_generation_service import TestGenerationService
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                test_service = TestGenerationService(db)
                test_result = await test_service.generate_and_run_tests(
                    repo=repository,
                    file_changes=file_changes,
                    repo_id=repository.id,
                )

                if not test_result.get("passed", False):
                    return {
                        "status": "tests_failed",
                        "test_id": test_result.get("test_id"),
                        "output": test_result.get("output"),
                        "message": "Generated tests failed. Review and fix before merging.",
                    }

                # Add test results to PR body
                pr_body += f"\n\n---\n### Auto-Generated Tests\nTests passed successfully. See test run for details."

        # 4. Execute GitHub Actions
        logger.info(f"Creating branch {branch_name} from {default_branch}...")
        await self.github_client.create_branch(
            full_name=repo_name,
            base_branch=default_branch,
            new_branch_name=branch_name,
        )

        logger.info(f"Committing {len(file_changes)} files to {branch_name}...")
        await self.github_client.create_commit(
            full_name=repo_name,
            branch_name=branch_name,
            file_changes=file_changes,
            commit_message=commit_message,
        )

        logger.info(f"Opening Pull Request: '{pr_title}'...")
        pr_result = await self.github_client.create_pull_request(
            full_name=repo_name,
            title=pr_title,
            body=pr_body,
            head_branch=branch_name,
            base_branch=default_branch,
        )

        return {
            "pr_url": pr_result["url"],
            "pr_number": pr_result["number"],
            "branch_name": branch_name,
        }
