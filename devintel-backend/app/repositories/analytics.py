"""Analytics repository."""

from datetime import datetime, timedelta
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Analytics
from app.models.chat import Chat
from app.models.repository import Repository
from app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[Analytics]):
    """Analytics repository."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        super().__init__(Analytics, db)

    async def get_by_user(self, user_id: UUID) -> Analytics | None:
        """Get analytics for a user."""
        result = await self.db.execute(
            select(Analytics).where(Analytics.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def increment_query_count(self, user_id: UUID, tokens: int = 0) -> Analytics:
        """Increment query count and token usage for a user."""
        from datetime import datetime

        analytics = await self.get_by_user(user_id)

        if not analytics:
            analytics = await self.create(
                user_id=user_id,
                query_count=1,
                token_usage=tokens,
                last_active_at=datetime.utcnow(),
            )
        else:
            analytics.query_count += 1
            analytics.token_usage += tokens
            analytics.last_active_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(analytics)

    async def increment_repositories_indexed(self, user_id: UUID) -> Analytics:
        """Increment repositories indexed count for a user."""
        from datetime import datetime

        analytics = await self.get_by_user(user_id)

        if not analytics:
            analytics = await self.create(
                user_id=user_id,
                repositories_indexed=1,
                last_active_at=datetime.utcnow(),
            )
        else:
            analytics.repositories_indexed += 1
            analytics.last_active_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(analytics)

        return analytics

    async def get_dashboard_stats(self, user_id: UUID) -> dict:
        """Get comprehensive stats for the user dashboard."""
        from datetime import datetime, timedelta, timezone
        
        # 1. Get totals from analytics table
        analytics = await self.get_by_user(user_id)
        if not analytics:
            return {
                "total_queries": 0,
                "total_tokens": 0,
                "total_repos_indexed": 0,
                "usage_trend": [],
                "top_repositories": [],
                "last_active_at": None,
            }

        # 2. Get usage trend (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        trend_query = (
            select(
                func.cast(Chat.created_at, func.date).label("date"),
                func.count(Chat.id).label("count")
            )
            .where(Chat.user_id == user_id, Chat.created_at >= seven_days_ago)
            .group_by(func.cast(Chat.created_at, func.date))
            .order_by(func.cast(Chat.created_at, func.date))
        )
        trend_result = await self.db.execute(trend_query)
        usage_trend = [
            {"date": row.date.strftime("%Y-%m-%d"), "queries": row.count}
            for row in trend_result
        ]

        # 3. Get top repositories by usage
        top_repos_query = (
            select(
                Repository.repo_name,
                func.count(Chat.id).label("count")
            )
            .join(Chat, Chat.repo_id == Repository.id)
            .where(Chat.user_id == user_id)
            .group_by(Repository.repo_name)
            .order_by(desc("count"))
            .limit(5)
        )
        top_repos_result = await self.db.execute(top_repos_query)
        top_repositories = [
            {"repo_name": row.repo_name, "queries": row.count}
            for row in top_repos_result
        ]

        return {
            "total_queries": analytics.query_count,
            "total_tokens": analytics.token_usage,
            "total_repos_indexed": analytics.repositories_indexed,
            "usage_trend": usage_trend,
            "top_repositories": top_repositories,
            "last_active_at": analytics.last_active_at,
        }
