"""File parsing utilities."""

from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def should_ignore_path(path: Path) -> bool:
    """Check if path should be ignored based on configuration."""
    # Match against individual path components, not substrings
    # e.g. "build" in ignored_dirs should match "/build/file.py" but not "/my_build_tools/file.py"
    path_parts = set(path.parts)

    for ignored_dir in settings.ignored_directories:
        if ignored_dir in path_parts:
            return True

    return False


def is_supported_file(file_path: Path) -> bool:
    """Check if file extension is supported."""
    return file_path.suffix in settings.supported_file_extensions


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)


def parse_repository_files(repo_path: str) -> list[tuple[str, str]]:
    """
    Parse repository and extract supported files.

    Returns:
        List of tuples (relative_path, file_content)
    """
    repo_path_obj = Path(repo_path)
    files_data = []

    for file_path in repo_path_obj.rglob("*"):
        if not file_path.is_file():
            continue

        if should_ignore_path(file_path):
            continue

        if not is_supported_file(file_path):
            continue

        if get_file_size_mb(file_path) > settings.max_file_size_mb:
            logger.warning(f"Skipping large file: {file_path} ({get_file_size_mb(file_path):.2f}MB)")
            continue

        try:
            # Try to read as text
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            relative_path = str(file_path.relative_to(repo_path_obj))
            files_data.append((relative_path, content))
            logger.debug(f"Parsed file: {relative_path}")

        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            continue

    logger.info(f"Parsed {len(files_data)} files from repository")
    return files_data
