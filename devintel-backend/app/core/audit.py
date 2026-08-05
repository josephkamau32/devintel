"""Audit logging — structured security event tracking.

Records security-relevant events (authentication, authorization,
data access, configuration changes) for compliance and forensics.

Events are logged to the structured logger (JSON format) with
a dedicated ``audit`` logger name for easy filtering/routing.

Usage::

    from app.core.audit import audit

    audit.log_auth_event("login_success", user_id="user-123", ip="1.2.3.4")
    audit.log_data_access("repo_read", user_id="user-123", resource_id="repo-456")
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from app.core.logging import get_logger

# Dedicated audit logger — separate from application logs
_audit_logger = get_logger("audit")


class AuditAction(str, Enum):
    """Categories of auditable actions."""

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    SIGNUP = "signup"

    # Authorization
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"

    # Data access
    REPO_CONNECT = "repo_connect"
    REPO_DELETE = "repo_delete"
    REPO_INDEX = "repo_index"
    DATA_EXPORT = "data_export"

    # AI operations
    AI_COMPLETION = "ai_completion"
    AI_PR_REVIEW = "ai_pr_review"
    AI_AUTO_FIX = "ai_auto_fix"
    AI_AGENT_ACTION = "ai_agent_action"

    # Admin
    CONFIG_CHANGE = "config_change"
    FEATURE_FLAG_CHANGE = "feature_flag_change"
    USER_ROLE_CHANGE = "user_role_change"


class AuditLog:
    """Structured audit event logger."""

    def log(
        self,
        action: str | AuditAction,
        *,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        severity: str = "info",
    ) -> None:
        """Log an audit event.

        Args:
            action: The action being audited.
            user_id: User performing the action.
            resource_type: Type of resource affected (e.g., "repository").
            resource_id: ID of the resource affected.
            ip_address: Client IP address.
            details: Additional context.
            severity: Log level ("info", "warning", "critical").
        """
        event = {
            "audit": True,
            "action": str(action),
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
        }

        if details:
            event["details"] = details

        log_method = getattr(_audit_logger, severity, _audit_logger.info)
        log_method(
            "AUDIT: %s user=%s resource=%s/%s",
            action, user_id or "system",
            resource_type or "-", resource_id or "-",
            extra=event,
        )

    def log_auth_event(
        self,
        action: str,
        *,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
        success: bool = True,
        details: Optional[dict] = None,
    ) -> None:
        """Convenience method for authentication events."""
        self.log(
            action,
            user_id=user_id,
            resource_type="auth",
            ip_address=ip,
            details=details,
            severity="info" if success else "warning",
        )

    def log_data_access(
        self,
        action: str,
        *,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: str = "repository",
        details: Optional[dict] = None,
    ) -> None:
        """Convenience method for data access events."""
        self.log(
            action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )

    def log_ai_event(
        self,
        action: str,
        *,
        user_id: Optional[str] = None,
        repo_id: Optional[str] = None,
        model: Optional[str] = None,
        tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
    ) -> None:
        """Convenience method for AI operation events."""
        self.log(
            action,
            user_id=user_id,
            resource_type="ai",
            resource_id=repo_id,
            details={
                k: v for k, v in {
                    "model": model,
                    "tokens": tokens,
                    "cost_usd": cost_usd,
                }.items() if v is not None
            },
        )


# Module-level singleton
audit = AuditLog()
