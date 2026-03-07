"""Auto-Fix Service - LLM-powered autonomous PR generation for Code Health issues."""

import json
import uuid
from typing import Any, Dict, List

from app.core.exceptions import APIError
from app.core.logging import get_logger
from app.integrations.github_client import GitHubClient
from app.integrations.openai_client import OpenAIClient
from app.models.repository import Repository
from app.models.user import User
from app.repositories.embedding import EmbeddingRepository
from app.services.embedding import EmbeddingService

logger = get_logger(__name__)


class AutoFixService:
    """Service to automatically generate and apply fixes for code health issues."""

    def __init__(self) -> None:
        self.openai_client = OpenAIClient()
        self.embedding_service = EmbeddingService()

    async def generate_and_apply_fix(
        self,
        repository: Repository,
        issue_description: str,
        user: User,
        embedding_repo: EmbeddingRepository,
    ) -> Dict[str, Any]:
        """
        End-to-end workflow to fix a code health issue.
        1. Find relevant files
        2. Read file content from GitHub
        3. Generate a fix via LLM
        4. Commit and open a PR
        """
        logger.info(f"Starting auto-fix for {repository.full_name}: {issue_description}")

        # Ensure we have a GitHub token for the user
        if not user.github_access_token:
            raise APIError("GitHub access token required for auto-fix.", status_code=400)

        github_client = GitHubClient(user.github_access_token)

        # 1. Search for relevant files using embeddings
        query_embedding = await self.embedding_service.generate_embedding(issue_description)
        hits = await embedding_repo.vector_search(
            repo_id=repository.id,
            query_embedding=query_embedding,
            top_k=3,
        )

        if not hits:
            raise APIError("Could not find relevant files in the codebase to fix this issue.", status_code=404)

        # Deduplicate files from chunks
        relevant_files = list({hit[0].file_path for hit in hits})
        logger.info(f"Identified relevant files for fix: {relevant_files}")

        # 2. Fetch current file contents from GitHub main branch
        # (Assuming the default branch represents the current state)
        file_contents = {}
        # Get repository details to find default branch
        repos_info = await github_client.get_user_repositories(per_page=100)
        repo_info = next((r for r in repos_info if r["full_name"] == repository.full_name), None)
        
        # We need the default branch to create a new branch from it
        # The PyGithub integration doesn't explicitly return default_branch in our wrapper,
        # so we'll fetch default branch dynamically or assume 'main'/'master'.
        # For safety, let's just use the PyGithub client directly to get the default branch.
        import asyncio
        from github import GithubException
        
        def _get_repo_details():
            repo = github_client.client.get_repo(repository.full_name)
            return {"default_branch": repo.default_branch}

        try:
            repo_details = await asyncio.to_thread(_get_repo_details)
            base_branch = repo_details["default_branch"]
        except GithubException as e:
            logger.error(f"Failed to get repo details: {e}")
            base_branch = "main" # Fallback

        for file_path in relevant_files:
            try:
                def _get_file_content(path=filepath):
                    repo = github_client.client.get_repo(repository.full_name)
                    contents = repo.get_contents(path, ref=base_branch)
                    return contents.decoded_content.decode("utf-8")
                
                content = await asyncio.to_thread(_get_file_content, path=file_path)
                file_contents[file_path] = content
            except Exception as e:
                logger.warning(f"Failed to read {file_path} from GitHub: {e}")

        if not file_contents:
            raise APIError("Failed to retrieve content for any relevant files.", status_code=500)

        # 3. Generate fix using LLM
        fix_plan = await self._generate_fix(repository.full_name, issue_description, file_contents)
        
        if not fix_plan or not fix_plan.get("modified_files"):
            raise APIError("AI could not generate a valid fix for this issue.", status_code=500)

        # 4. Apply fix (Branch -> Commit -> PR)
        branch_name = f"devintel/auto-fix-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Creating branch {branch_name} from {base_branch}")
        await github_client.create_branch(repository.full_name, base_branch, branch_name)

        # Prepare commit data
        commit_changes = []
        for modified_file in fix_plan["modified_files"]:
            path = modified_file["file_path"]
            new_content = modified_file["new_content"]
            commit_changes.append({"path": path, "content": new_content})

        logger.info(f"Committing {len(commit_changes)} files to {branch_name}")
        commit_message = f"Auto-Fix: {fix_plan.get('pr_title', 'Fix code health issue')}"
        await github_client.create_commit(
            full_name=repository.full_name,
            branch_name=branch_name,
            file_changes=commit_changes,
            commit_message=commit_message,
        )

        pr_title = f"🤖 Auto-Fix: {fix_plan.get('pr_title', issue_description)}"
        pr_body = (
            f"### DevIntel Auto-Fix\n\n"
            f"This PR was automatically generated to address the following code health issue:\n\n"
            f"> **{issue_description}**\n\n"
            f"#### Summary of Changes\n"
            f"{fix_plan.get('pr_summary', 'Applied automated fixes.')}\n\n"
            f"---\n"
            f"*Generated autonomously by DevIntel AI.*"
        )

        logger.info(f"Opening Pull Request for {branch_name}")
        pr_result = await github_client.create_pull_request(
            full_name=repository.full_name,
            title=pr_title,
            body=pr_body,
            head_branch=branch_name,
            base_branch=base_branch,
        )

        return {
            "status": "success",
            "pr_url": pr_result["url"],
            "pr_number": pr_result["number"],
            "branch_name": branch_name,
        }

    async def _generate_fix(self, repo_name: str, issue: str, file_contents: Dict[str, str]) -> Dict[str, Any]:
        """Call LLM to propose fixed code using Search/Replace blocks with a retry loop."""
        from app.utils.linter import check_syntax
        import re

        files_context = ""
        for path, content in file_contents.items():
            files_context += f"\n--- {path} ---\n{content}\n"

        system_prompt = f"""You are an elite Staff Software Engineer autonomously fixing a code issue in {repo_name}.

The identified issue is: "{issue}"

Here are the contents of the relevant files:
{files_context}

Your task is to fix the issue by modifying the necessary files. 
Instead of returning the entire file, you MUST return a Search and Replace block.

Respond ONLY with a valid JSON object matching this schema:
{{
  "pr_title": "<A concise, descriptive PR title>",
  "pr_summary": "<A brief summary of what you changed to fix the issue>",
  "modified_files": [
    {{
      "file_path": "<The exact path of the file you modified>",
      "search_block": "<The exact existing lines of code to replace>",
      "replace_block": "<The new lines of code to insert>"
    }}
  ]
}}

CRITICAL REQUIREMENTS FOR SEARCH BLOCKS:
1. The `search_block` MUST EXACTLY match a sequence of lines in the original file, including all whitespace and indentation.
2. The `search_block` must be unique within the file.
3. Include enough surrounding context lines in the `search_block` to ensure uniqueness.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate the fix for: {issue}"},
        ]
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.openai_client.chat_completion(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2500, 
                )
                raw = response.content if hasattr(response, "content") else str(response)
                
                content = raw.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1]
                    if content.endswith("```"):
                        content = content.rsplit("```", 1)[0]
                if content.startswith("json"):
                    content = content[4:].strip()
                
                fix_plan = json.loads(content)
                
                # Verify and apply the diff locally
                has_errors = False
                error_feedback = "Your previous attempt failed with the following errors:\n"
                
                for mod_file in fix_plan.get("modified_files", []):
                    path = mod_file["file_path"]
                    search = mod_file.get("search_block", "")
                    replace = mod_file.get("replace_block", "")
                    
                    if path not in file_contents:
                        has_errors = True
                        error_feedback += f"- File {path} was not in the provided context.\n"
                        continue
                        
                    orig_content = file_contents[path]
                    
                    if search not in orig_content:
                        # Try a more lenient search for whitespace issues
                        lenient_search = "\n".join([line.rstrip() for line in search.split('\n')])
                        if lenient_search not in "\n".join([line.rstrip() for line in orig_content.split('\n')]):
                            has_errors = True
                            error_feedback += f"- The search_block for {path} could not be found EXACTLY in the original file. Be extremely careful with indentation.\n"
                            continue
                    
                    # Apply diff in memory
                    mod_file["new_content"] = orig_content.replace(search, replace)
                    
                    # Run Linter
                    syntax_errors = check_syntax(path, mod_file["new_content"])
                    if syntax_errors:
                        has_errors = True
                        error_feedback += f"- Syntax errors in {path} after applying your fix:\n" + "\n".join(syntax_errors) + "\n"
                
                if not has_errors:
                    return fix_plan
                    
                logger.warning(f"Auto-Fix attempt {attempt+1} failed validation. Retrying...")
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": error_feedback + "\nPlease generate a new JSON fix plan that resolves these errors."})
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode failed on attempt {attempt+1}: {e}")
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": "Your response was not valid JSON. Please return ONLY a valid JSON object."})
            except Exception as e:
                logger.error(f"Failed to generate fix via LLM on attempt {attempt+1}: {e}")
                break

        return {}
