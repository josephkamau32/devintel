from fastapi import APIRouter
from app.api.v1 import auth, repositories, chat, health_score, pr_review, ws

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(repositories.router)
api_router.include_router(chat.router)
api_router.include_router(health_score.router)
api_router.include_router(pr_review.router)
api_router.include_router(pr_review.pulls_router)
api_router.include_router(ws.router)
