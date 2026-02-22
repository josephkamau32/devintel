"""Analytics repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Analytics
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
