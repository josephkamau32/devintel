"""User repository — consolidated into user_repo.py.

This file re-exports UserRepository for backward-compatibility with modules
that import from ``app.repositories.user``.
"""

from app.repositories.user_repo import UserRepository  # noqa: F401

__all__ = ["UserRepository"]
