"""Input validation and sanitization utilities."""

import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status

from app.core.logging import get_logger

logger = get_logger(__name__)


# SQL Injection Detection Patterns
SQL_INJECTION_PATTERNS = [
    r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b|\bALTER\b)",
    r"(--|\#|\/\*|\*\/)",  # SQL comments
    r"(\bOR\b.*=.*|AND.*=.*)",  # Common injection patterns
    r"(\bEXEC\b|\bEXECUTE\b)",
    r"(;.*\b(DROP|DELETE|UPDATE|INSERT)\b)",
    r"(\bxp_cmdshell\b)",
]

# Path Traversal Patterns
PATH_TRAVERSAL_PATTERNS = [
    r"\.\.",  # Parent directory
    r"~",  # Home directory
    r"\/\.\.",  # Unix path traversal
    r"\\\.\.",  # Windows path traversal
]


def detect_sql_injection(text: str, block: bool = True) -> bool:
    """
    Detect potential SQL injection attempts.
    
    Args:
        text: Input text to check
        block: If True, raises HTTPException on detection
        
    Returns:
        True if SQL injection pattern detected, False otherwise
        
    Raises:
        HTTPException: If block=True and injection detected
    """
    if not text:
        return False
    
    text_upper = text.upper()
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_upper, re.IGNORECASE):
            logger.warning(
                f"Potential SQL injection detected",
                extra={
                    "input": text[:100],  # Log first 100 chars only
                    "pattern": pattern,
                },
            )
            
            if block:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: Suspicious pattern detected",
                )
            
            return True
    
    return False


def sanitize_file_path(file_path: str, allowed_base_dirs: Optional[list[str]] = None) -> str:
    """
    Sanitize and validate file paths to prevent directory traversal.
    
    Args:
        file_path: Input file path
        allowed_base_dirs: List of allowed base directories (optional)
        
    Returns:
        Sanitized absolute path
        
    Raises:
        HTTPException: If path contains traversal patterns or is outside allowed dirs
    """
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path cannot be empty",
        )
    
    # Check for path traversal patterns
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, file_path):
            logger.warning(
                f"Path traversal attempt detected",
                extra={"input": file_path},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path: Path traversal not allowed",
            )
    
    try:
        # Resolve to absolute path
        resolved_path = Path(file_path).resolve()
        
        # Check if path is within allowed base directories
        if allowed_base_dirs:
            is_allowed = any(
                resolved_path.is_relative_to(Path(base_dir).resolve())
                for base_dir in allowed_base_dirs
            )
            
            if not is_allowed:
                logger.warning(
                    f"Access to path outside allowed directories",
                    extra={
                        "path": str(resolved_path),
                        "allowed_dirs": allowed_base_dirs,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to this path is not allowed",
                )
        
        return str(resolved_path)
        
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path",
        )


def validate_repository_name(repo_name: str) -> str:
    """
    Validate repository name format.
    
    Args:
        repo_name: Repository name (e.g., "owner/repo")
        
    Returns:
        Validated repository name
        
    Raises:
        HTTPException: If format is invalid
    """
    if not repo_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository name cannot be empty",
        )
    
    # GitHub repo format: owner/repo
    pattern = r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$"
    
    if not re.match(pattern, repo_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository name format. Expected: owner/repo",
        )
    
    # Check for SQL injection attempts
    detect_sql_injection(repo_name, block=True)
    
    return repo_name


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize general user input.
    
    Args:
        text: User input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        HTTPException: If input is too long or contains malicious patterns
    """
    if not text:
        return ""
    
    # Check length
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input too long. Maximum {max_length} characters allowed",
        )
    
    # Check for SQL injection
    detect_sql_injection(text, block=True)
    
    # Strip leading/trailing whitespace
    return text.strip()
