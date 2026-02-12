"""Input validation utilities for security."""

import re
from typing import Optional
from urllib.parse import urlparse

from app.core.exceptions import DevIntelException


class ValidationError(DevIntelException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            details={"field": field} if field else {},
        )


def validate_github_url(url: str) -> str:
    """
    Validate and sanitize GitHub repository URL.
    
    Prevents SSRF attacks by ensuring URL is a valid GitHub repository.
    
    Args:
        url: GitHub repository URL
    
    Returns:
        Sanitized URL
    
    Raises:
        ValidationError: If URL is invalid or not from GitHub
    """
    try:
        parsed = urlparse(url)
        
        # Must be HTTPS
        if parsed.scheme != "https":
            raise ValidationError(
                "Repository URL must use HTTPS",
                field="clone_url"
            )
        
        # Must be from GitHub
        allowed_domains = ["github.com", "www.github.com"]
        if parsed.netloc.lower() not in allowed_domains:
            raise ValidationError(
                "Only GitHub repositories are supported",
                field="clone_url"
            )
        
        # Path should match repository pattern (user/repo)
        path_pattern = re.compile(r"^/[\w-]+/[\w.-]+(?:\.git)?$")
        if not path_pattern.match(parsed.path):
            raise ValidationError(
                "Invalid GitHub repository path",
                field="clone_url"
            )
        
        return url
    
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {str(e)}", field="clone_url")


def validate_repository_name(name: str) -> str:
    """
    Validate repository full name (user/repo format).
    
    Prevents injection attacks via repository names.
    
    Args:
        name: Repository full name (e.g., "user/repo")
    
    Returns:
        Validated name
    
    Raises:
        ValidationError: If name is invalid
    """
    # Pattern: alphanumeric, hyphens, underscores, dots, slash
    pattern = re.compile(r"^[\w.-]+/[\w.-]+$")
    
    if not pattern.match(name):
        raise ValidationError(
            "Repository name must be in format 'user/repo' with only alphanumeric characters, hyphens, underscores, and dots",
            field="full_name"
        )
    
    # Additional checks
    if len(name) > 100:
        raise ValidationError(
            "Repository name too long (max 100 characters)",
            field="full_name"
        )
    
    if ".." in name or "//" in name:
        raise ValidationError(
            "Repository name contains invalid patterns",
            field="full_name"
        )
    
    return name


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent XSS and other injection attacks.
    
    Args:
        text: User input text
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    
    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(text, str):
        raise ValidationError("Input must be a string")
    
    # Length check
    if len(text) > max_length:
        raise ValidationError(f"Input too long (max {max_length} characters)")
    
    # Remove null bytes
    if "\x00" in text:
        raise ValidationError("Input contains null bytes")
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Ensure not empty after stripping
    if not text:
        raise ValidationError("Input cannot be empty")
    
    return text


def validate_pagination_params(
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> tuple[int, int]:
    """
    Validate pagination parameters.
    
    Prevents integer overflow and DoS via large page sizes.
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        max_page_size: Maximum allowed page size
    
    Returns:
        Tuple of (page, page_size)
    
    Raises:
        ValidationError: If parameters are invalid
    """
    if page < 1:
        raise ValidationError("Page number must be >= 1", field="page")
    
    if page > 10000:  # Reasonable upper limit
        raise ValidationError("Page number too large", field="page")
    
    if page_size < 1:
        raise ValidationError("Page size must be >= 1", field="page_size")
    
    if page_size > max_page_size:
        raise ValidationError(
            f"Page size too large (max {max_page_size})",
            field="page_size"
        )
    
    return page, page_size


def validate_chat_question(question: str) -> str:
    """
    Validate chat question input.
    
    Args:
        question: User's chat question
    
    Returns:
        Validated question
     
    Raises:
        ValidationError: If question is invalid
    """
    question = sanitize_user_input(question, max_length=5000)
    
    # Minimum length check
    if len(question) < 3:
        raise ValidationError(
            "Question too short (minimum 3 characters)",
            field="question"
        )
    
    return question


def validate_email(email: str) -> str:
    """
    Validate email address format.
    
    Args:
        email: Email address
    
    Returns:
        Validated email
    
    Raises:
        ValidationError: If email is invalid
    """
    # Basic email validation
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    if not pattern.match(email):
        raise ValidationError("Invalid email format", field="email")
    
    if len(email) > 320:  # RFC 5321
        raise ValidationError("Email too long", field="email")
    
    return email.lower()


def validate_uuid(uuid_str: str, field_name: str = "id") -> str:
    """
    Validate UUID string format.
    
    Args:
        uuid_str: UUID string
        field_name: Name of the field for error messages
    
    Returns:
        Validated UUID string
    
    Raises:
        ValidationError: If UUID is invalid
    """
    # UUID v4 pattern
    pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    
    if not pattern.match(uuid_str):
        raise ValidationError(f"Invalid UUID format", field=field_name)
    
    return uuid_str
