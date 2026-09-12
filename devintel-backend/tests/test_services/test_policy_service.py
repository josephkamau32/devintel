"""Tests for app.services.policy_service — custom code quality rules checker."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.policy import Policy, PolicyRuleType, PolicySeverity
from app.services.policy_service import PolicyChecker, PolicyViolation


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def checker(mock_db):
    with patch("app.services.policy_service.get_orchestrator") as mock_get_orch:
        mock_orch = MagicMock()
        mock_get_orch.return_value = mock_orch
        instance = PolicyChecker(mock_db)
        instance.orchestrator = mock_orch
        return instance


def make_policy(
    name="no-console-log",
    rule_type=PolicyRuleType.NO_PATTERN,
    severity=PolicySeverity.WARNING,
    config=None,
):
    p = MagicMock(spec=Policy)
    p.name = name
    p.rule_type = rule_type
    p.severity = severity
    p.config = config or {}
    return p


# ======================================================================
# _check_no_pattern
# ======================================================================

class TestCheckNoPattern:
    @pytest.mark.asyncio
    async def test_flags_added_matching_line(self, checker):
        policy = make_policy(
            name="ban-eval",
            config={
                "regex": r"\beval\(",
                "message": "Do not use eval()",
                "file": "app/main.py",
                "suggestion": "Use safer alternatives like ast.literal_eval",
            },
        )
        diff = """--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
 def run(code):
-    return None
+    result = eval(code)
     return result
"""
        violations = await checker._check_no_pattern(diff, policy)
        assert len(violations) == 1
        v = violations[0]
        assert isinstance(v, PolicyViolation)
        assert v.rule_name == "ban-eval"
        assert v.description == "Do not use eval()"
        assert v.suggestion == "Use safer alternatives like ast.literal_eval"
        assert v.file_path == "app/main.py"

    @pytest.mark.asyncio
    async def test_does_not_flag_deleted_or_context_lines(self, checker):
        """Pattern in deleted line or context line should NOT be flagged."""
        policy = make_policy(
            config={"regex": r"console\.log", "message": "No console.log"},
        )
        diff = """--- a/index.js
+++ b/index.js
@@ -1,3 +1,3 @@
 console.log("old context line");
-console.log("deleted line");
+logger.info("new clean line");
"""
        violations = await checker._check_no_pattern(diff, policy)
        assert violations == []

    @pytest.mark.asyncio
    async def test_does_not_flag_diff_headers(self, checker):
        """Lines starting with +++ are headers and should be ignored even if matching."""
        policy = make_policy(
            config={"regex": r"main\.py", "message": "no main.py"},
        )
        diff = "+++ b/src/main.py\n+clean line\n"
        violations = await checker._check_no_pattern(diff, policy)
        assert violations == []

    @pytest.mark.asyncio
    async def test_invalid_regex_returns_configuration_violation(self, checker):
        policy = make_policy(
            name="broken-regex",
            config={"regex": "[unclosed-bracket"},
        )
        diff = "+some line\n"
        violations = await checker._check_no_pattern(diff, policy)
        assert len(violations) == 1
        assert "Invalid regex in policy" in violations[0].description
        assert violations[0].file_path == "configuration"


# ======================================================================
# Stubs: _check_require_pattern, _check_complexity, _check_docstrings
# ======================================================================

class TestStubCheckers:
    @pytest.mark.asyncio
    async def test_require_pattern_returns_empty_list(self, checker):
        p = make_policy(rule_type=PolicyRuleType.REQUIRE_PATTERN)
        assert await checker._check_require_pattern("+code\n", p) == []

    @pytest.mark.asyncio
    async def test_complexity_returns_empty_list(self, checker):
        p = make_policy(rule_type=PolicyRuleType.MAX_COMPLEXITY)
        assert await checker._check_complexity("+code\n", p) == []

    @pytest.mark.asyncio
    async def test_docstrings_returns_empty_list(self, checker):
        p = make_policy(rule_type=PolicyRuleType.REQUIRE_DOCSTRINGS)
        assert await checker._check_docstrings("+code\n", p) == []


# ======================================================================
# _check_custom_prompt
# ======================================================================

class TestCheckCustomPrompt:
    @pytest.mark.asyncio
    async def test_empty_prompt_returns_empty(self, checker):
        p = make_policy(
            rule_type=PolicyRuleType.CUSTOM_PROMPT,
            config={"prompt": ""},
        )
        assert await checker._check_custom_prompt("+code\n", p) == []

    @pytest.mark.asyncio
    async def test_orchestrator_fail_triggers_violation(self, checker):
        p = make_policy(
            name="ai-rule",
            rule_type=PolicyRuleType.CUSTOM_PROMPT,
            severity=PolicySeverity.ERROR,
            config={"prompt": "Check if code has SQL injection"},
        )
        mock_resp = MagicMock()
        mock_resp.content = "FAIL: Potential SQL injection detected via string formatting"
        checker.orchestrator.complete = AsyncMock(return_value=mock_resp)

        violations = await checker._check_custom_prompt("+query = f'SELECT * FROM users WHERE id={user_id}'\n", p)
        assert len(violations) == 1
        assert violations[0].rule_name == "ai-rule"
        assert "FAIL" in violations[0].description
        assert violations[0].severity == PolicySeverity.ERROR

    @pytest.mark.asyncio
    async def test_orchestrator_pass_returns_no_violation(self, checker):
        p = make_policy(
            name="ai-rule",
            rule_type=PolicyRuleType.CUSTOM_PROMPT,
            config={"prompt": "Check code"},
        )
        mock_resp = MagicMock()
        mock_resp.content = "PASS: Code conforms to guidelines"
        checker.orchestrator.complete = AsyncMock(return_value=mock_resp)

        violations = await checker._check_custom_prompt("+query = 'SELECT 1'\n", p)
        assert violations == []

    @pytest.mark.asyncio
    async def test_orchestrator_error_handled_gracefully(self, checker):
        p = make_policy(
            rule_type=PolicyRuleType.CUSTOM_PROMPT,
            config={"prompt": "Check code"},
        )
        checker.orchestrator.complete = AsyncMock(side_effect=RuntimeError("AI timeout"))
        violations = await checker._check_custom_prompt("+code\n", p)
        assert violations == []


# ======================================================================
# check (end-to-end policy check for repo)
# ======================================================================

class TestPolicyCheckerCheck:
    @pytest.mark.asyncio
    async def test_check_aggregates_violations_from_all_policies(self, checker):
        repo_id = uuid4()
        p1 = make_policy(
            name="no-eval",
            rule_type=PolicyRuleType.NO_PATTERN,
            config={"regex": r"eval\(", "message": "No eval"},
        )
        p2 = make_policy(
            name="no-alert",
            rule_type=PolicyRuleType.NO_PATTERN,
            config={"regex": r"alert\(", "message": "No alert"},
        )

        with patch("app.services.policy_service.PolicyRepository") as mock_repo_cls:
            mock_repo_inst = MagicMock()
            mock_repo_inst.get_by_repo = AsyncMock(return_value=[p1, p2])
            mock_repo_cls.return_value = mock_repo_inst

            diff = "+eval('x')\n+alert('y')\n"
            violations = await checker.check(diff, repo_id)

            assert len(violations) == 2
            rule_names = {v.rule_name for v in violations}
            assert rule_names == {"no-eval", "no-alert"}
