"""PR Review Service — generates AI-powered code reviews using RAG context."""

import json
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.ai.orchestrator import get_orchestrator
from app.ai.response_parser import parse_json_response
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.services.embedding import EmbeddingService

logger = get_logger(__name__)

# Sentinel string embedded in every DevIntel review comment so we can
# detect whether a PR has already been reviewed (avoids duplicate comments).
REVIEW_WATERMARK = "<!-- devIntelReview -->"


class PRReviewService:
    """Autonomous code review service powered by RAG + OpenAI."""

    def __init__(self) -> None:
        self.orchestrator = get_orchestrator()
        self.embedding_service = EmbeddingService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_review(
        self,
        repository: Repository,
        pr_number: int,
        pr_title: str,
        changed_files: list[dict[str, Any]],
        embedding_repo: EmbeddingRepository,
    ) -> str:
        """
        Generate a structured markdown PR review.

        Steps:
        1. Build a compact diff summary (≤ 8 files, ≤ 120 lines each)
        2. Retrieve RAG context chunks for each changed file path
        3. Call OpenAI for a structured JSON review
        4. Render nicely formatted GitHub-markdown comment

        Returns:
            Formatted markdown string ready to post as a GitHub comment.
        """
        repo_name = repository.full_name

        # 1. Build diff summary (guard against massive PRs)
        diff_summary = self._build_diff_summary(changed_files, max_files=8, max_patch_lines=120)

        # 2. Retrieve RAG context for each changed file
        context_text = await self._retrieve_file_context(
            repo_id=repository.id,
            changed_files=changed_files,
            embedding_repo=embedding_repo,
        )

        # 3. Build prompt
        system_prompt = f"""You are DevIntel, an expert code reviewer for the repository: {repo_name}.

You are reviewing Pull Request #{pr_number}: "{pr_title}".

Existing codebase context:
{context_text}

Diff of changes in this PR:
{diff_summary}

Your task: perform a thorough, production-grade code review.
Respond with ONLY valid JSON matching this exact schema:
{{
  "overall_verdict": "LGTM" | "LGTM with nits" | "Needs Changes" | "Request Changes",
  "summary": "<2-4 sentence high-level summary of what the PR does>",
  "risk_level": "low" | "medium" | "high",
  "positive_aspects": ["<point>", ...],
  "issues": [
    {{
      "severity": "critical" | "major" | "minor" | "nit",
      "file": "<filename or 'general'>",
      "description": "<clear description of the issue>",
      "suggestion": "<concrete fix or improvement>"
    }},
    ...
  ],
  "security_concerns": ["<concern>", ...],
  "performance_notes": ["<note>", ...],
  "test_coverage_note": "<observation about test coverage>"
}}
Be specific, cite file names. Keep each issue description under 100 words."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please review PR #{pr_number}: {pr_title}"},
        ]

        logger.info(f"Calling AI orchestrator for PR review: {repo_name}#{pr_number}")
        response = await self.orchestrator.complete(
            messages=messages,
            temperature=0.1,
            max_tokens=2000,
            agent="pr_review",
        )

        # Parse JSON response
        raw_content = response.content
        review_data = self._parse_review_json(raw_content)

        # 4. Render as GitHub markdown
        return self._render_markdown(pr_number, pr_title, review_data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_diff_summary(
        self,
        changed_files: list[dict[str, Any]],
        max_files: int = 8,
        max_patch_lines: int = 120,
    ) -> str:
        """Build a compact diff summary, capping size for the LLM context."""
        lines = []
        total_additions = sum(f.get("additions", 0) for f in changed_files)
        total_deletions = sum(f.get("deletions", 0) for f in changed_files)
        lines.append(
            f"Total: {len(changed_files)} files changed, "
            f"+{total_additions} -{total_deletions}\n"
        )

        for i, file_info in enumerate(changed_files[:max_files]):
            filename = file_info.get("filename", "unknown")
            status = file_info.get("status", "modified")
            additions = file_info.get("additions", 0)
            deletions = file_info.get("deletions", 0)
            patch = file_info.get("patch", "")

            lines.append(f"\n--- {filename} [{status}] +{additions} -{deletions} ---")
            if patch:
                patch_lines = patch.split("\n")[:max_patch_lines]
                lines.append("\n".join(patch_lines))
                if len(patch.split("\n")) > max_patch_lines:
                    lines.append(f"... (truncated, {len(patch.split(chr(10)))} lines total)")

        if len(changed_files) > max_files:
            remaining = len(changed_files) - max_files
            lines.append(f"\n... and {remaining} more file(s) not shown.")

        return "\n".join(lines)

    async def _retrieve_file_context(
        self,
        repo_id: UUID,
        changed_files: list[dict[str, Any]],
        embedding_repo: EmbeddingRepository,
    ) -> str:
        """
        For each changed file, retrieve the top-2 most similar chunks from the
        existing codebase index to give the LLM background context.
        """
        context_parts: list[str] = []
        seen_chunks: set[str] = set()

        for file_info in changed_files[:6]:  # Limit to 6 files to stay within context budget
            filename = file_info.get("filename", "")
            if not filename:
                continue

            try:
                query_embedding = await self.embedding_service.generate_embedding(filename)
                results = await embedding_repo.vector_search(
                    repo_id=repo_id,
                    query_embedding=query_embedding,
                    top_k=2,
                )
                for emb, _sim in results:
                    key = f"{emb.file_path}:{emb.chunk_index}"
                    if key not in seen_chunks:
                        seen_chunks.add(key)
                        context_parts.append(
                            f"\n--- Existing: {emb.file_path} ---\n{emb.chunk_text[:600]}"
                        )
            except Exception as exc:
                logger.warning(f"Failed to retrieve context for {filename}: {exc}")

        return "\n".join(context_parts) if context_parts else "[No existing indexed context found]"

    def _parse_review_json(self, raw_content: str) -> dict[str, Any]:
        """Extract and parse JSON from the LLM response, with fallbacks."""
        # Strip markdown code fences if present
        content = raw_content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Find JSON object boundaries
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass

        logger.warning("Failed to parse review JSON, using fallback")
        return {
            "overall_verdict": "Review Generated",
            "summary": raw_content[:500],
            "risk_level": "medium",
            "positive_aspects": [],
            "issues": [],
            "security_concerns": [],
            "performance_notes": [],
            "test_coverage_note": "Unable to assess.",
        }

    def _render_markdown(
        self,
        pr_number: int,
        pr_title: str,
        data: dict[str, Any],
    ) -> str:
        """Render structured review data as a rich GitHub markdown comment."""
        verdict = data.get("overall_verdict", "Review Completed")
        risk = data.get("risk_level", "medium")
        summary = data.get("summary", "")
        positives = data.get("positive_aspects", [])
        issues = data.get("issues", [])
        security = data.get("security_concerns", [])
        performance = data.get("performance_notes", [])
        test_note = data.get("test_coverage_note", "")

        # Verdict emoji & color badge
        verdict_emoji = {
            "LGTM": "✅",
            "LGTM with nits": "✅",
            "Needs Changes": "⚠️",
            "Request Changes": "❌",
        }.get(verdict, "🔍")

        risk_badge = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}.get(risk, risk)

        severity_emoji = {
            "critical": "🔴",
            "major": "🟠",
            "minor": "🟡",
            "nit": "⚪",
        }

        lines = [
            REVIEW_WATERMARK,
            f"## {verdict_emoji} DevIntel AI Code Review",
            "",
            f"**Verdict:** {verdict} &nbsp;|&nbsp; **Risk:** {risk_badge}",
            "",
            "### 📋 Summary",
            summary,
            "",
        ]

        if positives:
            lines += ["### 👍 Positive Aspects", ""]
            for p in positives:
                lines.append(f"- {p}")
            lines.append("")

        if issues:
            lines += ["### 🔍 Issues Found", ""]
            for issue in issues:
                sev = issue.get("severity", "minor")
                emoji = severity_emoji.get(sev, "⚪")
                file_ref = issue.get("file", "general")
                desc = issue.get("description", "")
                suggestion = issue.get("suggestion", "")
                lines.append(
                    f"{emoji} **[{sev.upper()}]** `{file_ref}`  \n"
                    f"{desc}"
                )
                if suggestion:
                    lines.append(f"> 💡 *Suggestion: {suggestion}*")
                lines.append("")
        else:
            lines += ["### ✅ No Issues Found", ""]

        if security:
            lines += ["### 🔐 Security Concerns", ""]
            for s in security:
                lines.append(f"- ⚠️ {s}")
            lines.append("")

        if performance:
            lines += ["### ⚡ Performance Notes", ""]
            for p in performance:
                lines.append(f"- {p}")
            lines.append("")

        if test_note:
            lines += ["### 🧪 Test Coverage", test_note, ""]

        lines += [
            "---",
            "*🤖 Generated by [DevIntel AI](https://github.com/josephkamau32/devintel) — "
            "autonomous code intelligence platform*",
        ]

        return "\n".join(lines)
