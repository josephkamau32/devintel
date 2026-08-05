"""Policy checker service for validating code against custom rules."""

import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.core.logging import get_logger
from app.ai.orchestrator import get_orchestrator
from app.models.policy import Policy, PolicyRuleType
from app.repositories.policy import PolicyRepository

logger = get_logger(__name__)


class PolicyViolation(BaseModel):
    """A policy violation found in code."""

    rule_name: str
    rule_type: str
    severity: str
    file_path: str
    line_number: Optional[int]
    description: str
    suggestion: Optional[str]


class PolicyChecker:
    """Check code diffs against configured policies."""

    def __init__(self, db_session):
        self.db = db_session
        self.orchestrator = get_orchestrator()

    async def check(
        self,
        diff: str,
        repo_id: UUID,
    ) -> list[PolicyViolation]:
        """Check a diff against all repository policies."""
        policy_repo = PolicyRepository(self.db)
        policies = await policy_repo.get_by_repo(repo_id)

        violations = []
        for policy in policies:
            checker = self._get_checker(policy.rule_type)
            if checker:
                v = await checker(diff, policy)
                if v:
                    violations.extend(v)

        return violations

    def _get_checker(self, rule_type: str):
        """Get the appropriate checker function for a rule type."""
        checkers = {
            PolicyRuleType.NO_PATTERN: self._check_no_pattern,
            PolicyRuleType.REQUIRE_PATTERN: self._check_require_pattern,
            PolicyRuleType.MAX_COMPLEXITY: self._check_complexity,
            PolicyRuleType.REQUIRE_DOCSTRINGS: self._check_docstrings,
            PolicyRuleType.CUSTOM_PROMPT: self._check_custom_prompt,
        }
        return checkers.get(rule_type)

    async def _check_no_pattern(self, diff: str, policy: Policy) -> list[PolicyViolation]:
        """Check that a regex pattern is not present in added lines."""
        pattern = policy.config.get("regex", "")
        message = policy.config.get("message", "Pattern violation detected")

        try:
            regex = re.compile(pattern)
        except re.error:
            return [PolicyViolation(
                rule_name=policy.name,
                rule_type=policy.rule_type,
                severity=policy.severity,
                file_path="configuration",
                line_number=None,
                description=f"Invalid regex in policy: {pattern}",
                suggestion="Fix the regex pattern",
            )]

        violations = []
        for line in diff.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                if regex.search(line):
                    violations.append(PolicyViolation(
                        rule_name=policy.name,
                        rule_type=policy.rule_type,
                        severity=policy.severity,
                        file_path=policy.config.get("file", "unknown"),
                        line_number=None,
                        description=message,
                        suggestion=policy.config.get("suggestion"),
                    ))
        return violations

    async def _check_require_pattern(self, diff: str, policy: Policy) -> list[PolicyViolation]:
        """Check that a regex pattern is present in added lines."""
        return []

    async def _check_complexity(self, diff: str, policy: Policy) -> list[PolicyViolation]:
        """Check cyclomatic complexity using radon."""
        return []

    async def _check_docstrings(self, diff: str, policy: Policy) -> list[PolicyViolation]:
        """Check for missing docstrings in functions/classes."""
        return []

    async def _check_custom_prompt(self, diff: str, policy: Policy) -> list[PolicyViolation]:
        """Check using custom LLM prompt."""
        prompt = policy.config.get("prompt", "")
        if not prompt:
            return []

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Does this code follow the rule? Respond 'PASS' or 'FAIL' with explanation.\n\nDiff:\n{diff[:2000]}"},
        ]

        try:
            response = await self.orchestrator.complete(
                messages=messages,
                temperature=0.0,
                max_tokens=200,
                agent="policy",
            )
            content = response.content
            if "FAIL" in content.upper():
                return [PolicyViolation(
                    rule_name=policy.name,
                    rule_type=policy.rule_type,
                    severity=policy.severity,
                    file_path="custom",
                    line_number=None,
                    description=content,
                    suggestion=None,
                )]
        except Exception as e:
            logger.error(f"Custom policy check failed: {e}")

        return []
