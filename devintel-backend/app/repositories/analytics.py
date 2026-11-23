"""Analytics repository."""

from datetime import UTC
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Analytics
from app.models.chat import Chat
from app.models.repository import IndexingStatus, Repository
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
                last_active_at=datetime.now(UTC),
            )
        else:
            analytics.query_count += 1
            analytics.token_usage += tokens
            analytics.last_active_at = datetime.now(UTC)
            await self.db.flush()
            await self.db.refresh(analytics)

        return analytics

    async def increment_repositories_indexed(self, user_id: UUID) -> Analytics:
        """Increment repositories indexed count for a user."""
        from datetime import datetime

        analytics = await self.get_by_user(user_id)

        if not analytics:
            analytics = await self.create(
                user_id=user_id,
                repositories_indexed=1,
                last_active_at=datetime.now(UTC),
            )
        else:
            analytics.repositories_indexed += 1
            analytics.last_active_at = datetime.now(UTC)
            await self.db.flush()
            await self.db.refresh(analytics)

        return analytics

    async def get_dashboard_stats(self, user_id: UUID) -> dict[str, Any]:
        """Get comprehensive stats for the user dashboard derived from real data."""
        from datetime import datetime, timedelta

        # 1. Total repos indexed: count user's repos whose status is complete
        repos_stmt = select(func.count(Repository.id)).where(
            Repository.user_id == user_id,
            Repository.indexing_status.in_([IndexingStatus.COMPLETE, "complete", "completed"]),
        )
        repos_res = await self.db.execute(repos_stmt)
        total_repos_indexed = repos_res.scalar() or 0

        # 2. Total queries from Chat records
        queries_stmt = select(func.count(Chat.id)).where(Chat.user_id == user_id)
        queries_res = await self.db.execute(queries_stmt)
        total_queries = queries_res.scalar() or 0

        # 3. Total tokens from Chat records
        tokens_stmt = select(func.coalesce(func.sum(Chat.token_usage), 0)).where(Chat.user_id == user_id)
        tokens_res = await self.db.execute(tokens_stmt)
        total_tokens = int(tokens_res.scalar() or 0)

        # 4. Last active timestamp from Chat records, falling back to Analytics table
        last_active_stmt = select(func.max(Chat.created_at)).where(Chat.user_id == user_id)
        last_active_res = await self.db.execute(last_active_stmt)
        last_active_at = last_active_res.scalar()
        if not last_active_at:
            analytics = await self.get_by_user(user_id)
            last_active_at = analytics.last_active_at if analytics else None

        # 5. Usage trend (last 7 days) from Chat records
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        trend_query = (
            select(
                func.date(Chat.created_at).label("day"),
                func.count(Chat.id).label("count"),
            )
            .where(Chat.user_id == user_id, Chat.created_at >= seven_days_ago)
            .group_by(func.date(Chat.created_at))
            .order_by(func.date(Chat.created_at))
        )
        trend_result = await self.db.execute(trend_query)
        usage_trend = [
            {
                "date": row.day.strftime("%Y-%m-%d") if hasattr(row.day, "strftime") else str(row.day),
                "queries": row.count,
            }
            for row in trend_result
        ]

        # 6. Top repositories by usage from Chat records
        top_repos_query = (
            select(
                Repository.repo_name,
                func.count(Chat.id).label("count"),
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
            "total_queries": total_queries,
            "total_tokens": total_tokens,
            "total_repos_indexed": total_repos_indexed,
            "usage_trend": usage_trend,
            "top_repositories": top_repositories,
            "last_active_at": last_active_at,
        }
