"""Analytics routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import AnalyticsDashboard

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get real-time analytics for the user dashboard."""
    analytics_repo = AnalyticsRepository(db)
    try:
        stats = await analytics_repo.get_dashboard_stats(current_user.id)
        return stats
    except Exception as e:
        import logging
        logging.error(f"Failed to fetch analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics dashboard data",
        )
