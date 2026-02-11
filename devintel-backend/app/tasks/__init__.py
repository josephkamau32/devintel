"""Tasks package."""

from app.tasks.celery import celery
from app.tasks.indexing import index_repository_task

__all__ = ["celery", "index_repository_task"]
