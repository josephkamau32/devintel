"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

# Create Celery app
celery = Celery(
    "devintel",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
)

# Auto-discover tasks
celery.autodiscover_tasks(["app.tasks"])
