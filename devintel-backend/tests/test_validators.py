"""Test input validators."""

import pytest
from fastapi import HTTPException

from app.core.validators import (
    detect_sql_injection,
    sanitize_file_path,
    validate_repository_name,
    sanitize_user_input,
)


def test_detect_sql_injection_safe():
    """Test SQL injection detection with safe input."""
    safe_input = "normal query text"
    result = detect_sql_injection(safe_input, block=False)
    assert result is False


def test_detect_sql_injection_unsafe():
    """Test SQL injection detection with malicious input."""
    malicious_input = "SELECT * FROM users WHERE id=1 OR 1=1"
    result = detect_sql_injection(malicious_input, block=False)
    assert result is True


def test_detect_sql_injection_blocks_unsafe():
    """Test SQL injection blocking."""
    malicious_input = "'; DROP TABLE users; --"
    with pytest.raises(HTTPException) as exc_info:
        detect_sql_injection(malicious_input, block=True)
    
    assert exc_info.value.status_code == 400


def test_sanitize_file_path_safe():
    """Test path sanitization with safe path."""
    safe_path = "/home/user/project/file.py"
    result = sanitize_file_path(safe_path)
    assert isinstance(result, str)


def test_sanitize_file_path_traversal():
    """Test path sanitization blocks traversal."""
    malicious_path = "../../../etc/passwd"
    with pytest.raises(HTTPException) as exc_info:
        sanitize_file_path(malicious_path)
    
    assert exc_info.value.status_code == 400


def test_validate_repository_name_valid():
    """Test repository name validation with valid input."""
    valid_name = "owner/repo-name"
    result = validate_repository_name(valid_name)
    assert result == valid_name


def test_validate_repository_name_invalid():
    """Test repository name validation with invalid input."""
    invalid_name = "invalid format"
    with pytest.raises(HTTPException) as exc_info:
        validate_repository_name(invalid_name)
    
    assert exc_info.value.status_code == 400


def test_sanitize_user_input():
    """Test user input sanitization."""
    user_input = "  This is a test input  "
    result = sanitize_user_input(user_input)
    assert result == "This is a test input"


def test_sanitize_user_input_too_long():
    """Test user input length validation."""
    long_input = "a" * 10001
    with pytest.raises(HTTPException) as exc_info:
        sanitize_user_input(long_input)
    
    assert exc_info.value.status_code == 400
