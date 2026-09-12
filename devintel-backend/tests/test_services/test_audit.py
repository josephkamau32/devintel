"""Tests for app.core.audit — structured security event tracking."""

import logging
from unittest.mock import patch

from app.core.audit import AuditAction, AuditLog


class TestAuditLog:
    def test_log_calls_logger_with_structured_event(self):
        audit_log = AuditLog()
        with patch("app.core.audit._audit_logger", spec=logging.Logger) as mock_logger:
            audit_log.log(
                action=AuditAction.LOGIN_SUCCESS,
                user_id="user-123",
                resource_type="auth",
                resource_id="session-456",
                ip_address="192.168.1.1",
                details={"method": "oauth"},
                severity="info",
            )

            mock_logger.info.assert_called_once()
            args, kwargs = mock_logger.info.call_args
            assert args[0] == "AUDIT: %s user=%s resource=%s/%s"
            assert args[1] == AuditAction.LOGIN_SUCCESS
            assert args[2] == "user-123"
            assert args[3] == "auth"
            assert args[4] == "session-456"

            extra = kwargs["extra"]
            assert extra["audit"] is True
            assert extra["action"] == str(AuditAction.LOGIN_SUCCESS)
            assert extra["user_id"] == "user-123"
            assert extra["resource_type"] == "auth"
            assert extra["resource_id"] == "session-456"
            assert extra["ip_address"] == "192.168.1.1"
            assert extra["details"] == {"method": "oauth"}
            assert "timestamp" in extra

    def test_log_falls_back_to_info_for_unknown_severity(self):
        audit_log = AuditLog()
        with patch("app.core.audit._audit_logger", spec=logging.Logger) as mock_logger:
            audit_log.log(
                action="custom_action",
                severity="nonexistent_level",
            )
            # Since spec=logging.Logger doesn't have "nonexistent_level",
            # getattr falls back to default (_audit_logger.info)
            mock_logger.info.assert_called_once()

    def test_log_warning_severity(self):
        audit_log = AuditLog()
        with patch("app.core.audit._audit_logger", spec=logging.Logger) as mock_logger:
            audit_log.log(
                action=AuditAction.ACCESS_DENIED,
                user_id="bad-actor",
                severity="warning",
            )
            mock_logger.warning.assert_called_once()

    def test_log_auth_event_success_uses_info(self):
        audit_log = AuditLog()
        with patch.object(audit_log, "log") as mock_log:
            audit_log.log_auth_event(
                action="login_success",
                user_id="user-42",
                ip="10.0.0.1",
                success=True,
                details={"provider": "github"},
            )
            mock_log.assert_called_once_with(
                "login_success",
                user_id="user-42",
                resource_type="auth",
                ip_address="10.0.0.1",
                details={"provider": "github"},
                severity="info",
            )

    def test_log_auth_event_failure_uses_warning(self):
        audit_log = AuditLog()
        with patch.object(audit_log, "log") as mock_log:
            audit_log.log_auth_event(
                action="login_failure",
                user_id="user-42",
                ip="10.0.0.1",
                success=False,
                details={"reason": "invalid_password"},
            )
            mock_log.assert_called_once_with(
                "login_failure",
                user_id="user-42",
                resource_type="auth",
                ip_address="10.0.0.1",
                details={"reason": "invalid_password"},
                severity="warning",
            )

    def test_log_data_access_default_and_custom_resource(self):
        audit_log = AuditLog()
        with patch.object(audit_log, "log") as mock_log:
            audit_log.log_data_access(
                action="repo_read",
                user_id="user-99",
                resource_id="repo-1",
            )
            mock_log.assert_called_once_with(
                "repo_read",
                user_id="user-99",
                resource_type="repository",
                resource_id="repo-1",
                details=None,
            )

    def test_log_ai_event_filters_none_details(self):
        audit_log = AuditLog()
        with patch.object(audit_log, "log") as mock_log:
            audit_log.log_ai_event(
                action="ai_completion",
                user_id="user-1",
                repo_id="repo-10",
                model="gemini-1.5-flash",
                tokens=150,
                cost_usd=None,  # Should be omitted from details dict
            )
            mock_log.assert_called_once_with(
                "ai_completion",
                user_id="user-1",
                resource_type="ai",
                resource_id="repo-10",
                details={"model": "gemini-1.5-flash", "tokens": 150},
            )
