from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    architecture,
    auth,
    chat,
    collaboration,
    cross_repo,
    git_history,
    health_score,
    migration,
    organizations,
    policies,
    pr_review,
    repositories,
    webhooks,
    ws,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(repositories.router)
api_router.include_router(chat.router)
api_router.include_router(health_score.router)
api_router.include_router(pr_review.router)
api_router.include_router(pr_review.pulls_router)
api_router.include_router(ws.router)
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(analytics.router)
api_router.include_router(architecture.router)
api_router.include_router(collaboration.router)
api_router.include_router(cross_repo.router)
api_router.include_router(git_history.router)
api_router.include_router(migration.router)
api_router.include_router(policies.router)
api_router.include_router(webhooks.router)
