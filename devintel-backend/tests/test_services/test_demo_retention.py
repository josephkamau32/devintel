"""Tests for demo chat retention and privacy scrubbing."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.repository import IndexingStatus, Repository
from app.models.user import User
from app.services.auth_service import DEMO_EMAIL, AuthService
from app.services.chat import DEMO_CHAT_RETENTION_MARKER, scrub_demo_chat_retention


@pytest.mark.asyncio
async def test_old_demo_chats_scrubbed_and_still_counted(
    db_session: AsyncSession,
):
    """Old demo chat rows (>7 days) have their text scrubbed but remain counted in analytics."""
    # Ensure demo user exists
    user_res = await db_session.execute(select(User).where(User.email == DEMO_EMAIL))
    demo_user = user_res.scalar_one_or_none()
    if not demo_user:
        demo_user = User(
            email=DEMO_EMAIL,
            full_name="Demo User",
            is_active=True,
            is_verified=True,
        )
        db_session.add(demo_user)
        await db_session.commit()
        await db_session.refresh(demo_user)

    repo = Repository(
        repo_name="devintel",
        full_name="josephkamau32/devintel",
        user_id=demo_user.id,
        indexing_status=IndexingStatus.COMPLETE,
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    other_user = User(
        email="regular@example.com",
        full_name="Regular User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    now = datetime.now(UTC)
    eight_days_ago = now - timedelta(days=8)
    two_days_ago = now - timedelta(days=2)

    # 1. Create an old demo chat (8 days ago)
    old_demo_chat = Chat(
        user_id=demo_user.id,
        repo_id=repo.id,
        question="How does auth work?",
        response="Auth uses PyJWT and bcrypt.",
        agent_type="chat",
        token_usage=250,
        input_tokens=150,
        output_tokens=100,
        created_at=eight_days_ago,
    )

    # 2. Create a recent demo chat (2 days ago)
    recent_demo_chat = Chat(
        user_id=demo_user.id,
        repo_id=repo.id,
        question="What is the database?",
        response="Neon PostgreSQL 16.",
        agent_type="chat",
        token_usage=180,
        input_tokens=100,
        output_tokens=80,
        created_at=two_days_ago,
    )

    # 3. Create an old chat for ANOTHER user (10 days ago)
    other_user_chat = Chat(
        user_id=other_user.id,
        repo_id=repo.id,
        question="Sensitive secret query from regular user",
        response="Sensitive answer for regular user",
        agent_type="chat",
        token_usage=300,
        input_tokens=200,
        output_tokens=100,
        created_at=now - timedelta(days=10),
    )

    db_session.add_all([old_demo_chat, recent_demo_chat, other_user_chat])
    await db_session.commit()
    await db_session.refresh(old_demo_chat)
    await db_session.refresh(recent_demo_chat)
    await db_session.refresh(other_user_chat)

    # Run scrubbing
    scrubbed_count = await scrub_demo_chat_retention(db_session, demo_email=DEMO_EMAIL, retention_days=7)
    assert scrubbed_count == 1

    # Verify old demo chat was scrubbed
    await db_session.refresh(old_demo_chat)
    assert old_demo_chat.question == DEMO_CHAT_RETENTION_MARKER
    assert old_demo_chat.response == DEMO_CHAT_RETENTION_MARKER
    assert old_demo_chat.token_usage == 250
    assert old_demo_chat.input_tokens == 150
    assert old_demo_chat.output_tokens == 100
    created_at = old_demo_chat.created_at if old_demo_chat.created_at.tzinfo else old_demo_chat.created_at.replace(tzinfo=UTC)
    assert created_at == eight_days_ago

    # Verify recent demo chat was untouched
    await db_session.refresh(recent_demo_chat)
    assert recent_demo_chat.question == "What is the database?"
    assert recent_demo_chat.response == "Neon PostgreSQL 16."
    assert recent_demo_chat.token_usage == 180

    # Verify other user's old chat was untouched
    await db_session.refresh(other_user_chat)
    assert other_user_chat.question == "Sensitive secret query from regular user"
    assert other_user_chat.response == "Sensitive answer for regular user"
    assert other_user_chat.token_usage == 300

    # Verify dashboard metrics still count the scrubbed demo chat
    from app.repositories.analytics import AnalyticsRepository
    analytics_repo = AnalyticsRepository(db_session)
    stats = await analytics_repo.get_dashboard_stats(demo_user.id)
    # Both demo chats (old + recent) are counted
    assert stats["total_queries"] == 2
    assert stats["total_tokens"] == 430  # 250 + 180
    assert stats["total_repos_indexed"] == 1


@pytest.mark.asyncio
async def test_demo_retention_idempotent(db_session: AsyncSession):
    """Running demo retention multiple times is idempotent."""
    user_res = await db_session.execute(select(User).where(User.email == DEMO_EMAIL))
    demo_user = user_res.scalar_one_or_none()
    if not demo_user:
        demo_user = User(
            email=DEMO_EMAIL,
            full_name="Demo User",
            is_active=True,
            is_verified=True,
        )
        db_session.add(demo_user)
        await db_session.commit()
        await db_session.refresh(demo_user)

    repo = Repository(
        repo_name="devintel",
        full_name="josephkamau32/devintel",
        user_id=demo_user.id,
        indexing_status=IndexingStatus.COMPLETE,
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    chat = Chat(
        user_id=demo_user.id,
        repo_id=repo.id,
        question="Old question",
        response="Old answer",
        agent_type="chat",
        token_usage=100,
        created_at=datetime.now(UTC) - timedelta(days=9),
    )
    db_session.add(chat)
    await db_session.commit()

    # First run scrubs 1
    count1 = await scrub_demo_chat_retention(db_session, demo_email=DEMO_EMAIL, retention_days=7)
    assert count1 == 1

    # Second run scrubs 0
    count2 = await scrub_demo_chat_retention(db_session, demo_email=DEMO_EMAIL, retention_days=7)
    assert count2 == 0


@pytest.mark.asyncio
async def test_demo_login_triggers_retention_scrubbing(db_session: AsyncSession):
    """Calling demo_login automatically scrubs expired demo chats."""
    auth_service = AuthService(db_session)
    user, _, _ = await auth_service.demo_login()

    repo = Repository(
        repo_name="devintel",
        full_name="josephkamau32/devintel",
        user_id=user.id,
        indexing_status=IndexingStatus.COMPLETE,
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    old_chat = Chat(
        user_id=user.id,
        repo_id=repo.id,
        question="To be scrubbed on login",
        response="To be scrubbed on login",
        agent_type="chat",
        token_usage=100,
        created_at=datetime.now(UTC) - timedelta(days=12),
    )
    db_session.add(old_chat)
    await db_session.commit()
    await db_session.refresh(old_chat)

    # Next demo login triggers retention scrubbing
    await auth_service.demo_login()

    await db_session.refresh(old_chat)
    assert old_chat.question == DEMO_CHAT_RETENTION_MARKER
    assert old_chat.response == DEMO_CHAT_RETENTION_MARKER
    assert old_chat.token_usage == 100
