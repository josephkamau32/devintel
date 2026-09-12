"""Tests for app.core.constants and app.schemas (user, generated_test)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

import app.core.constants as constants
from app.schemas.generated_test import (
    GeneratedTestResponse,
    TestGenerateRequest,
    TestGenerateResponse,
    TestListResult,
    TestRegenerateRequest,
)
from app.schemas.user import UserPublic


class TestCoreConstants:
    def test_rag_and_embedding_constants(self):
        assert constants.EMBEDDING_DIMENSIONS == 768
        assert constants.DEFAULT_CHUNK_SIZE > 0
        assert constants.DEFAULT_CHUNK_OVERLAP < constants.DEFAULT_CHUNK_SIZE
        assert constants.DEFAULT_TOP_K == 6

    def test_file_extensions_and_ignored_directories(self):
        assert ".py" in constants.SUPPORTED_EXTENSIONS
        assert ".ts" in constants.SUPPORTED_EXTENSIONS
        assert ".tsx" in constants.SUPPORTED_EXTENSIONS
        assert "node_modules" in constants.IGNORED_DIRS
        assert ".git" in constants.IGNORED_DIRS
        assert ".venv" in constants.IGNORED_DIRS

    def test_rate_limiting_and_security_constants(self):
        assert constants.MIN_PASSWORD_LENGTH >= 8
        assert constants.MAX_LOGIN_ATTEMPTS >= 3
        assert "minute" in constants.AUTH_RATE_LIMIT
        assert "minute" in constants.CHAT_RATE_LIMIT


class TestUserSchemas:
    def test_user_public_valid_model(self):
        uid = uuid4()
        user = UserPublic(
            id=uid,
            email="dev@example.com",
            full_name="Jane Dev",
            github_username="janedev",
            avatar_url="https://example.com/avatar.png",
            is_verified=True,
        )
        assert user.id == uid
        assert user.email == "dev@example.com"
        assert user.is_verified is True

    def test_user_public_optional_fields(self):
        uid = uuid4()
        user = UserPublic(
            id=uid,
            email=None,
            full_name=None,
            github_username=None,
            avatar_url=None,
            is_verified=False,
        )
        assert user.email is None
        assert user.is_verified is False


class TestGeneratedTestSchemas:
    def test_generated_test_response_model(self):
        tid = uuid4()
        rid = uuid4()
        now = datetime.now(timezone.utc)
        resp = GeneratedTestResponse(
            id=tid,
            repo_id=rid,
            draft_pr_id=None,
            file_path="tests/test_sample.py",
            test_content="def test_foo(): assert True",
            status="passed",
            output="1 passed in 0.01s",
            created_at=now,
            updated_at=now,
        )
        assert resp.id == tid
        assert resp.status == "passed"
        assert resp.draft_pr_id is None

    def test_test_generate_request_and_response(self):
        rid = uuid4()
        req = TestGenerateRequest(
            repository_id=rid,
            file_changes=[{"file": "app/main.py", "patch": "+# comment"}],
        )
        assert req.repository_id == rid
        assert len(req.file_changes) == 1

        res = TestGenerateResponse(
            test_id="test-123",
            passed=True,
            output="Generated 3 tests successfully",
        )
        assert res.test_id == "test-123"
        assert res.passed is True

    def test_test_list_result_and_regenerate_request(self):
        rid = uuid4()
        tid = uuid4()
        now = datetime.now(timezone.utc)
        test_item = GeneratedTestResponse(
            id=tid,
            repo_id=rid,
            draft_pr_id=None,
            file_path="tests/test_x.py",
            test_content="def test_x(): pass",
            status="pending",
            output=None,
            created_at=now,
            updated_at=now,
        )
        list_res = TestListResult(tests=[test_item])
        assert len(list_res.tests) == 1
        assert list_res.tests[0].id == tid

        regen = TestRegenerateRequest(
            repository_id=rid,
            test_id=tid,
            file_changes=[],
        )
        assert regen.test_id == tid
