"""
Tests for CodeHealthService — covers context building, JSON parsing, default
scoring, and the full analyze() orchestration with mocked dependencies.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.repository import Repository
from app.services.code_health_service import PROBE_QUERIES, CodeHealthService

# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def service() -> CodeHealthService:
    with (
        patch("app.services.code_health_service.OpenAIClient"),
        patch("app.services.code_health_service.EmbeddingService"),
    ):
        svc = CodeHealthService()
    return svc


@pytest.fixture
def sample_repo() -> Repository:
    return Repository(
        id=uuid4(),
        repo_name="backend",
        full_name="acme/backend",
        url="https://github.com/acme/backend",
        user_id=uuid4(),
        indexed_status=True,
        language="Python",
    )


@pytest.fixture
def valid_health_json() -> dict:
    return {
        "overall_score": 78.5,
        "complexity_score": 72.0,
        "documentation_score": 65.0,
        "maintainability_score": 80.0,
        "test_coverage_score": 55.0,
        "security_score": 90.0,
        "summary": "Well-structured codebase with good security practices. Test coverage needs improvement.",
        "top_issues": ["Low test coverage in auth module", "Several TODO comments"],
        "recommendations": ["Add unit tests for auth", "Resolve TODO comments"],
    }


@pytest.fixture
def mock_chunk():
    """A fake Embedding ORM object."""
    chunk = MagicMock()
    chunk.id = uuid4()
    chunk.file_path = "app/services/auth.py"
    chunk.chunk_text = "def authenticate(token: str) -> User:\n    pass"
    return chunk


# ─── _build_context ───────────────────────────────────────────────────────────

class TestBuildContext:
    def test_respects_max_chars(self, service, mock_chunk):
        """Context must not exceed max_chars."""
        chunks = [mock_chunk] * 50
        result = service._build_context(chunks, max_chars=500)
        assert len(result) <= 500 + 200  # allow for header lines

    def test_empty_chunks(self, service):
        assert service._build_context([]) == ""

    def test_includes_file_paths(self, service, mock_chunk):
        result = service._build_context([mock_chunk])
        assert "app/services/auth.py" in result

    def test_includes_chunk_text(self, service, mock_chunk):
        result = service._build_context([mock_chunk])
        assert "def authenticate" in result

    def test_truncates_long_chunk_text(self, service):
        """Each chunk's text is capped at 400 chars in the context."""
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.file_path = "big.py"
        chunk.chunk_text = "x" * 1000
        result = service._build_context([chunk], max_chars=99999)
        # Should contain at most 400 x's from this chunk
        assert result.count("x") <= 400


# ─── _parse_json ─────────────────────────────────────────────────────────────

class TestParseJson:
    def test_valid_json(self, service, valid_health_json):
        raw = json.dumps(valid_health_json)
        result = service._parse_json(raw)
        assert result["overall_score"] == 78.5
        assert result["security_score"] == 90.0

    def test_strips_json_markdown_fence(self, service, valid_health_json):
        raw = f"```json\n{json.dumps(valid_health_json)}\n```"
        result = service._parse_json(raw)
        assert result["overall_score"] == 78.5

    def test_strips_plain_markdown_fence(self, service, valid_health_json):
        raw = f"```\n{json.dumps(valid_health_json)}\n```"
        result = service._parse_json(raw)
        assert "overall_score" in result

    def test_invalid_returns_defaults(self, service):
        result = service._parse_json("Not valid JSON whatsoever.")
        # Should return the default 50.0 scores dict
        assert result["overall_score"] == 50.0
        assert result["complexity_score"] == 50.0

    def test_partial_json_extracted(self, service, valid_health_json):
        """JSON surrounded by extra text should still be extracted."""
        raw = f"Analysis complete: {json.dumps(valid_health_json)} Thank you."
        result = service._parse_json(raw)
        assert result["overall_score"] == 78.5


# ─── _default_result ─────────────────────────────────────────────────────────

class TestDefaultResult:
    def test_has_all_six_dimension_keys(self, service):
        result = service._default_result()
        required_keys = {
            "overall_score",
            "complexity_score",
            "documentation_score",
            "maintainability_score",
            "test_coverage_score",
            "security_score",
        }
        assert required_keys.issubset(result.keys())

    def test_all_scores_are_50(self, service):
        result = service._default_result()
        for key in ["overall_score", "complexity_score", "documentation_score",
                    "maintainability_score", "test_coverage_score", "security_score"]:
            assert result[key] == 50.0

    def test_has_summary_and_lists(self, service):
        result = service._default_result()
        assert isinstance(result["top_issues"], list)
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["summary"], str)


# ─── _record_to_dict ─────────────────────────────────────────────────────────

class TestRecordToDict:
    def test_deserializes_json_lists(self, service):
        record = MagicMock()
        record.id = uuid4()
        record.repo_id = uuid4()
        record.overall_score = 75.0
        record.complexity_score = 70.0
        record.documentation_score = 60.0
        record.maintainability_score = 80.0
        record.test_coverage_score = 50.0
        record.security_score = 85.0
        record.summary = "Good."
        record.top_issues = json.dumps(["issue A", "issue B"])
        record.recommendations = json.dumps(["rec 1"])
        record.language_detected = "Python"
        record.files_analyzed = 12
        record.computed_at = None

        result = service._record_to_dict(record)

        assert isinstance(result["top_issues"], list)
        assert result["top_issues"] == ["issue A", "issue B"]
        assert result["recommendations"] == ["rec 1"]
        assert result["overall_score"] == 75.0
        assert result["computed_at"] is None

    def test_handles_empty_json_lists(self, service):
        record = MagicMock()
        record.id = uuid4()
        record.repo_id = uuid4()
        record.overall_score = 50.0
        record.complexity_score = record.documentation_score = 50.0
        record.maintainability_score = record.test_coverage_score = record.security_score = 50.0
        record.summary = ""
        record.top_issues = "[]"
        record.recommendations = "[]"
        record.language_detected = None
        record.files_analyzed = 0
        record.computed_at = None

        result = service._record_to_dict(record)
        assert result["top_issues"] == []
        assert result["recommendations"] == []


# ─── PROBE_QUERIES constant ──────────────────────────────────────────────────

def test_probe_queries_coverage():
    """At least 10 probe queries must exist to cover diverse semantic regions."""
    assert len(PROBE_QUERIES) >= 10

def test_probe_queries_are_non_empty_strings():
    for q in PROBE_QUERIES:
        assert isinstance(q, str) and len(q) > 0


# ─── analyze() integration ───────────────────────────────────────────────────

class TestAnalyze:
    @pytest.mark.asyncio
    async def test_analyze_full_pipeline(
        self, service, sample_repo, mock_chunk, valid_health_json
    ):
        """Happy path: chunks found → LLM called → health_repo.upsert() called."""
        mock_embedding_repo = MagicMock()
        mock_embedding_repo.vector_search = AsyncMock(return_value=[(mock_chunk, 0.9)])

        mock_health_repo = MagicMock()
        # upsert returns an ORM-like record
        upserted = MagicMock()
        upserted.id = uuid4()
        upserted.repo_id = sample_repo.id
        upserted.overall_score = valid_health_json["overall_score"]
        upserted.complexity_score = valid_health_json["complexity_score"]
        upserted.documentation_score = valid_health_json["documentation_score"]
        upserted.maintainability_score = valid_health_json["maintainability_score"]
        upserted.test_coverage_score = valid_health_json["test_coverage_score"]
        upserted.security_score = valid_health_json["security_score"]
        upserted.summary = valid_health_json["summary"]
        upserted.top_issues = json.dumps(valid_health_json["top_issues"])
        upserted.recommendations = json.dumps(valid_health_json["recommendations"])
        upserted.language_detected = "Python"
        upserted.files_analyzed = 1
        upserted.computed_at = None
        mock_health_repo.upsert = AsyncMock(return_value=upserted)

        service.embedding_service = MagicMock()
        service.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 1536)

        mock_llm_response = MagicMock()
        mock_llm_response.content = json.dumps(valid_health_json)
        service.openai_client = MagicMock()
        service.openai_client.chat_completion = AsyncMock(return_value=mock_llm_response)

        result = await service.analyze(
            repository=sample_repo,
            embedding_repo=mock_embedding_repo,
            health_repo=mock_health_repo,
        )

        # Verify upsert was called
        mock_health_repo.upsert.assert_called_once()
        # Verify result has expected top-level keys
        assert "overall_score" in result
        assert "top_issues" in result
        assert isinstance(result["top_issues"], list)

    @pytest.mark.asyncio
    async def test_analyze_empty_repo_uses_defaults(self, service, sample_repo):
        """When no chunks are found, defaults are persisted without calling LLM."""
        mock_embedding_repo = MagicMock()
        mock_embedding_repo.vector_search = AsyncMock(return_value=[])

        mock_health_repo = MagicMock()
        upserted = MagicMock()
        upserted.id = uuid4()
        upserted.repo_id = sample_repo.id
        upserted.overall_score = 50.0
        upserted.complexity_score = upserted.documentation_score = 50.0
        upserted.maintainability_score = upserted.test_coverage_score = upserted.security_score = 50.0
        upserted.summary = "Analysis could not be completed."
        upserted.top_issues = "[]"
        upserted.recommendations = "[]"
        upserted.language_detected = None
        upserted.files_analyzed = 0
        upserted.computed_at = None
        mock_health_repo.upsert = AsyncMock(return_value=upserted)

        service.embedding_service = MagicMock()
        service.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 1536)

        # LLM should NOT be called when no chunks available
        service.openai_client = MagicMock()
        service.openai_client.chat_completion = AsyncMock()

        await service.analyze(
            repository=sample_repo,
            embedding_repo=mock_embedding_repo,
            health_repo=mock_health_repo,
        )

        mock_health_repo.upsert.assert_called_once()
        service.openai_client.chat_completion.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_deduplicates_chunks(self, service, sample_repo, valid_health_json):
        """Same chunk id returned from multiple probes should only appear once."""
        shared_id = uuid4()
        chunk = MagicMock()
        chunk.id = shared_id
        chunk.file_path = "shared.py"
        chunk.chunk_text = "shared code"

        # All probe queries return the exact same chunk
        mock_embedding_repo = MagicMock()
        mock_embedding_repo.vector_search = AsyncMock(return_value=[(chunk, 0.95)])

        mock_health_repo = MagicMock()
        upserted = MagicMock()
        upserted.id = uuid4()
        upserted.repo_id = sample_repo.id
        upserted.overall_score = 78.5
        upserted.complexity_score = upserted.documentation_score = 70.0
        upserted.maintainability_score = upserted.test_coverage_score = upserted.security_score = 70.0
        upserted.summary = "ok"
        upserted.top_issues = "[]"
        upserted.recommendations = "[]"
        upserted.language_detected = "Python"
        upserted.files_analyzed = 1
        upserted.computed_at = None
        mock_health_repo.upsert = AsyncMock(return_value=upserted)

        service.embedding_service = MagicMock()
        service.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 1536)

        mock_llm_response = MagicMock()
        mock_llm_response.content = json.dumps(valid_health_json)
        service.openai_client = MagicMock()
        service.openai_client.chat_completion = AsyncMock(return_value=mock_llm_response)

        await service.analyze(
            repository=sample_repo,
            embedding_repo=mock_embedding_repo,
            health_repo=mock_health_repo,
        )

        call_kwargs = mock_health_repo.upsert.call_args[1]
        # Even though all 10 probes return the same chunk, files_analyzed should be 1
        assert call_kwargs["data"]["files_analyzed"] == 1
