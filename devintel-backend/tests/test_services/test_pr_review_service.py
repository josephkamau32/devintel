"""
Tests for PRReviewService — covers diff summarisation, JSON parsing, markdown
rendering, and the full generate_review() orchestration with mocked dependencies.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.pr_review_service import PRReviewService, REVIEW_WATERMARK
from app.models.repository import Repository


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def service() -> PRReviewService:
    """Create a PRReviewService with mocked internal clients."""
    with (
        patch("app.services.pr_review_service.OpenAIClient"),
        patch("app.services.pr_review_service.EmbeddingService"),
    ):
        svc = PRReviewService()
    return svc


@pytest.fixture
def sample_repo() -> Repository:
    return Repository(
        id=uuid4(),
        repo_name="my-service",
        full_name="acme/my-service",
        url="https://github.com/acme/my-service",
        user_id=uuid4(),
        indexed_status=True,
    )


@pytest.fixture
def sample_changed_files():
    return [
        {
            "filename": "app/auth.py",
            "status": "modified",
            "additions": 20,
            "deletions": 5,
            "patch": "\n".join([f"+ line {i}" for i in range(200)]),  # 200 patch lines
        },
        {
            "filename": "tests/test_auth.py",
            "status": "added",
            "additions": 50,
            "deletions": 0,
            "patch": "+ def test_login(): pass",
        },
    ]


@pytest.fixture
def valid_review_json() -> dict:
    return {
        "overall_verdict": "LGTM",
        "summary": "Clean PR that adds proper JWT validation.",
        "risk_level": "low",
        "positive_aspects": ["Good separation of concerns", "Proper error handling"],
        "issues": [
            {
                "severity": "nit",
                "file": "app/auth.py",
                "description": "Unused import `os`",
                "suggestion": "Remove the unused import.",
            }
        ],
        "security_concerns": [],
        "performance_notes": ["Consider caching the public key lookup"],
        "test_coverage_note": "Tests cover the happy path but miss expiry edge cases.",
    }


# ─── _build_diff_summary ─────────────────────────────────────────────────────

class TestBuildDiffSummary:
    def test_truncates_long_patches(self, service, sample_changed_files):
        """Patches longer than max_patch_lines must be truncated."""
        summary = service._build_diff_summary(sample_changed_files, max_patch_lines=10)
        # 200 patch lines → only 10 shown + truncation note
        assert "truncated" in summary
        assert "app/auth.py" in summary

    def test_caps_number_of_files(self, service):
        """Only the first max_files files should appear in the summary."""
        big_pr = [
            {"filename": f"file_{i}.py", "status": "modified", "additions": 1, "deletions": 0, "patch": ""}
            for i in range(15)
        ]
        summary = service._build_diff_summary(big_pr, max_files=5)
        assert "file_0.py" in summary
        assert "file_5.py" not in summary
        assert "10 more file(s)" in summary

    def test_includes_file_stats(self, service, sample_changed_files):
        """Summary must include filename, status, and ± counts."""
        summary = service._build_diff_summary(sample_changed_files)
        assert "+20" in summary
        assert "-5" in summary
        assert "modified" in summary

    def test_totals_line_present(self, service, sample_changed_files):
        """First line should contain total files changed count."""
        summary = service._build_diff_summary(sample_changed_files)
        assert "2 files changed" in summary


# ─── _parse_review_json ───────────────────────────────────────────────────────

class TestParseReviewJson:
    def test_valid_json(self, service, valid_review_json):
        raw = json.dumps(valid_review_json)
        result = service._parse_review_json(raw)
        assert result["overall_verdict"] == "LGTM"
        assert result["risk_level"] == "low"

    def test_strips_markdown_fence(self, service, valid_review_json):
        raw = f"```json\n{json.dumps(valid_review_json)}\n```"
        result = service._parse_review_json(raw)
        assert result["overall_verdict"] == "LGTM"

    def test_strips_plain_code_fence(self, service, valid_review_json):
        raw = f"```\n{json.dumps(valid_review_json)}\n```"
        result = service._parse_review_json(raw)
        assert "overall_verdict" in result

    def test_extracts_json_from_prose(self, service, valid_review_json):
        """JSON embedded inside prose text should still be extracted."""
        raw = f"Here is the review: {json.dumps(valid_review_json)} That's all."
        result = service._parse_review_json(raw)
        assert result["overall_verdict"] == "LGTM"

    def test_invalid_json_returns_fallback(self, service):
        result = service._parse_review_json("This is not JSON at all!!!")
        # Fallback must still return a structurally valid review dict
        assert "overall_verdict" in result
        assert "issues" in result
        assert "summary" in result


# ─── _render_markdown ─────────────────────────────────────────────────────────

class TestRenderMarkdown:
    def test_contains_watermark(self, service, valid_review_json):
        md = service._render_markdown(42, "Add JWT auth", valid_review_json)
        assert REVIEW_WATERMARK in md

    def test_lgtm_verdict_shows_checkmark(self, service, valid_review_json):
        md = service._render_markdown(42, "Add JWT auth", valid_review_json)
        assert "✅" in md
        assert "LGTM" in md

    def test_request_changes_shows_cross(self, service, valid_review_json):
        data = {**valid_review_json, "overall_verdict": "Request Changes"}
        md = service._render_markdown(1, "Risky change", data)
        assert "❌" in md

    def test_issues_rendered_with_severity(self, service, valid_review_json):
        md = service._render_markdown(42, "Add JWT auth", valid_review_json)
        assert "NIT" in md
        assert "app/auth.py" in md
        assert "Unused import" in md

    def test_security_section_present_when_non_empty(self, service, valid_review_json):
        data = {**valid_review_json, "security_concerns": ["Hardcoded secret detected"]}
        md = service._render_markdown(1, "PR", data)
        assert "Security" in md
        assert "Hardcoded secret" in md

    def test_no_issues_renders_ok_section(self, service, valid_review_json):
        data = {**valid_review_json, "issues": []}
        md = service._render_markdown(1, "Clean PR", data)
        assert "No Issues Found" in md

    def test_risk_badge_present(self, service, valid_review_json):
        md = service._render_markdown(1, "PR", valid_review_json)
        assert "🟢 Low" in md  # risk_level = "low"


# ─── generate_review() integration ───────────────────────────────────────────

class TestGenerateReview:
    @pytest.mark.asyncio
    async def test_generate_review_returns_markdown_string(
        self, service, sample_repo, sample_changed_files, valid_review_json
    ):
        """Full pipeline: embedding + openai mocked → returns markdown."""
        mock_embedding_repo = MagicMock()
        mock_embedding_repo.vector_search = AsyncMock(return_value=[])

        service.embedding_service = MagicMock()
        service.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 1536)

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review_json)
        service.openai_client = MagicMock()
        service.openai_client.chat_completion = AsyncMock(return_value=mock_response)

        result = await service.generate_review(
            repository=sample_repo,
            pr_number=17,
            pr_title="Add JWT authentication",
            changed_files=sample_changed_files,
            embedding_repo=mock_embedding_repo,
        )

        assert isinstance(result, str)
        assert REVIEW_WATERMARK in result
        assert "LGTM" in result

    @pytest.mark.asyncio
    async def test_generate_review_calls_vector_search_per_file(
        self, service, sample_repo, sample_changed_files, valid_review_json
    ):
        """embedding_repo.vector_search should be called once per changed file (≤6)."""
        mock_embedding_repo = MagicMock()
        mock_embedding_repo.vector_search = AsyncMock(return_value=[])

        service.embedding_service = MagicMock()
        service.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 1536)

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review_json)
        service.openai_client = MagicMock()
        service.openai_client.chat_completion = AsyncMock(return_value=mock_response)

        await service.generate_review(
            repository=sample_repo,
            pr_number=1,
            pr_title="Test PR",
            changed_files=sample_changed_files,
            embedding_repo=mock_embedding_repo,
        )

        # 2 changed files → 2 vector_search calls
        assert mock_embedding_repo.vector_search.call_count == len(sample_changed_files)

    @pytest.mark.asyncio
    async def test_generate_review_handles_openai_failure_gracefully(
        self, service, sample_repo, sample_changed_files
    ):
        """Even if LLM returns unparseable content, the review is still a string."""
        mock_embedding_repo = MagicMock()
        mock_embedding_repo.vector_search = AsyncMock(return_value=[])

        service.embedding_service = MagicMock()
        service.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 1536)

        mock_response = MagicMock()
        mock_response.content = "Sorry, I cannot generate a review right now."
        service.openai_client = MagicMock()
        service.openai_client.chat_completion = AsyncMock(return_value=mock_response)

        result = await service.generate_review(
            repository=sample_repo,
            pr_number=3,
            pr_title="Broken PR",
            changed_files=sample_changed_files,
            embedding_repo=mock_embedding_repo,
        )

        assert isinstance(result, str)
        assert REVIEW_WATERMARK in result

    @pytest.mark.asyncio
    async def test_generate_review_caps_files_at_six_for_rag(
        self, service, sample_repo, valid_review_json
    ):
        """RAG context retrieval is limited to 6 files regardless of PR size."""
        many_files = [
            {"filename": f"src/module_{i}.py", "status": "modified",
             "additions": 1, "deletions": 0, "patch": ""}
            for i in range(10)
        ]

        mock_embedding_repo = MagicMock()
        mock_embedding_repo.vector_search = AsyncMock(return_value=[])

        service.embedding_service = MagicMock()
        service.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 1536)

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review_json)
        service.openai_client = MagicMock()
        service.openai_client.chat_completion = AsyncMock(return_value=mock_response)

        await service.generate_review(
            repository=sample_repo,
            pr_number=5,
            pr_title="Giant PR",
            changed_files=many_files,
            embedding_repo=mock_embedding_repo,
        )

        # vector_search must be called at most 6 times
        assert mock_embedding_repo.vector_search.call_count <= 6
