"""Tests for atomic staging swap and rollback in seed_demo.py."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import ArchitectureDiagram
from app.models.code_health import CodeHealth
from app.models.embedding import Embedding
from app.models.repository import IndexingStatus, Repository
from app.models.user import User
from scripts.seed_demo import (
    DEMO_EMAIL,
    DEMO_REPO_FULL_NAME,
    DEMO_STAGING_REPO_FULL_NAME,
    atomic_swap_staging_to_live,
    check_git_preconditions,
    cleanup_staging_repo,
)


@pytest.mark.asyncio
async def test_atomic_swap_staging_to_live(db_session: AsyncSession):
    """Verify atomic_swap_staging_to_live moves all child rows and deletes staging."""
    # 1. Create demo user
    user = User(
        email=DEMO_EMAIL,
        full_name="Demo User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Create live repository with old data
    live_repo = Repository(
        user_id=user.id,
        full_name=DEMO_REPO_FULL_NAME,
        repo_name="devintel",
        description="Old description",
        indexing_status=IndexingStatus.INDEXING,
        indexing_progress=50,
    )
    db_session.add(live_repo)
    await db_session.commit()
    await db_session.refresh(live_repo)

    live_health = CodeHealth(
        repo_id=live_repo.id,
        overall_score=45.0,
        complexity_score=40.0,
        documentation_score=50.0,
        maintainability_score=45.0,
        test_coverage_score=45.0,
        security_score=45.0,
        summary="Old health summary",
        files_analyzed=10,
        computed_at=datetime.now(UTC),
    )
    live_arch = ArchitectureDiagram(
        repo_id=live_repo.id,
        name="Old Architecture",
        diagram_type="mermaid",
        mermaid_code="graph TD; Old-->A;",
    )
    live_emb = Embedding(
        repo_id=live_repo.id,
        file_path="app/old.py",
        chunk_index=0,
        chunk_text="old chunk",
        embedding=[0.1] * 768,
    )
    db_session.add_all([live_health, live_arch, live_emb])
    await db_session.commit()

    # 3. Create staging repository with new data
    staging_repo = Repository(
        user_id=user.id,
        full_name=DEMO_STAGING_REPO_FULL_NAME,
        repo_name="devintel-staging",
        description="Staging description",
        indexing_status=IndexingStatus.INDEXING,
        indexing_progress=90,
    )
    db_session.add(staging_repo)
    await db_session.commit()
    await db_session.refresh(staging_repo)

    staging_health = CodeHealth(
        repo_id=staging_repo.id,
        overall_score=88.5,
        complexity_score=85.0,
        documentation_score=90.0,
        maintainability_score=88.0,
        test_coverage_score=87.0,
        security_score=92.0,
        summary="New health summary",
        files_analyzed=66,
        computed_at=datetime.now(UTC),
    )
    staging_arch = ArchitectureDiagram(
        repo_id=staging_repo.id,
        name="DevIntel Core Architecture",
        diagram_type="mermaid",
        mermaid_code="graph TD; New-->B;",
    )
    staging_emb = Embedding(
        repo_id=staging_repo.id,
        file_path="app/ai/orchestrator.py",
        chunk_index=0,
        chunk_text="new chunk",
        embedding=[0.9] * 768,
    )
    db_session.add_all([staging_health, staging_arch, staging_emb])
    await db_session.commit()

    # 4. Perform atomic swap
    live_id = live_repo.id
    staging_id = staging_repo.id
    new_desc = "Snapshot of backend modules app/ai, app/services and app/models at commit c50f697"
    await atomic_swap_staging_to_live(
        session=db_session,
        live_repo_id=live_id,
        staging_repo_id=staging_id,
        demo_repo_desc=new_desc,
    )

    # 5. Assertions
    # Staging repo must be deleted
    staging_res = await db_session.execute(
        select(Repository).where(Repository.id == staging_id)
    )
    assert staging_res.scalar_one_or_none() is None

    # Live repo must be updated with identical ID
    live_res = await db_session.execute(
        select(Repository).where(Repository.id == live_id)
    )
    updated_live_repo = live_res.scalar_one()
    assert updated_live_repo.id == live_id
    assert updated_live_repo.description == new_desc
    assert updated_live_repo.indexing_status == IndexingStatus.COMPLETE
    assert updated_live_repo.indexing_progress == 100

    # Child records under live repo must now reflect staging records
    health_res = await db_session.execute(
        select(CodeHealth).where(CodeHealth.repo_id == live_id)
    )
    health = health_res.scalar_one()
    assert health.overall_score == 88.5
    assert health.summary == "New health summary"

    arch_res = await db_session.execute(
        select(ArchitectureDiagram).where(ArchitectureDiagram.repo_id == live_id)
    )
    arch = arch_res.scalar_one()
    assert arch.name == "DevIntel Core Architecture"
    assert arch.mermaid_code == "graph TD; New-->B;"

    emb_res = await db_session.execute(
        select(Embedding).where(Embedding.repo_id == live_id)
    )
    emb = emb_res.scalar_one()
    assert emb.file_path == "app/ai/orchestrator.py"

    # No child records should remain under staging_repo.id
    staging_embs = await db_session.execute(
        select(func.count()).select_from(Embedding).where(Embedding.repo_id == staging_id)
    )
    assert staging_embs.scalar_one() == 0


@pytest.mark.asyncio
async def test_cleanup_staging_repo(db_session: AsyncSession):
    """Verify cleanup_staging_repo deletes only staging repository and leaves live repo intact."""
    user = User(
        email=DEMO_EMAIL,
        full_name="Demo User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    live_repo = Repository(
        user_id=user.id,
        full_name=DEMO_REPO_FULL_NAME,
        repo_name="devintel",
        description="Preserved description",
        indexing_status=IndexingStatus.COMPLETE,
        indexing_progress=100,
    )
    staging_repo = Repository(
        user_id=user.id,
        full_name=DEMO_STAGING_REPO_FULL_NAME,
        repo_name="devintel-staging",
        description="Staging to delete",
        indexing_status=IndexingStatus.INDEXING,
        indexing_progress=20,
    )
    db_session.add_all([live_repo, staging_repo])
    await db_session.commit()
    await db_session.refresh(live_repo)
    await db_session.refresh(staging_repo)

    live_emb = Embedding(
        repo_id=live_repo.id,
        file_path="app/live.py",
        chunk_index=0,
        chunk_text="live chunk",
        embedding=[0.5] * 768,
    )
    staging_emb = Embedding(
        repo_id=staging_repo.id,
        file_path="app/staging.py",
        chunk_index=0,
        chunk_text="staging chunk",
        embedding=[0.5] * 768,
    )
    db_session.add_all([live_emb, staging_emb])
    await db_session.commit()

    # Trigger cleanup of staging
    staging_id = staging_repo.id
    live_id = live_repo.id
    await cleanup_staging_repo(db_session, staging_repo_id=staging_id)

    # Staging must be gone
    st_repo_res = await db_session.execute(
        select(Repository).where(Repository.id == staging_id)
    )
    assert st_repo_res.scalar_one_or_none() is None
    st_emb_res = await db_session.execute(
        select(func.count()).select_from(Embedding).where(Embedding.repo_id == staging_id)
    )
    assert st_emb_res.scalar_one() == 0

    # Live repo and its embeddings must remain intact
    live_repo_res = await db_session.execute(
        select(Repository).where(Repository.id == live_id)
    )
    assert live_repo_res.scalar_one() is not None
    live_emb_res = await db_session.execute(
        select(func.count()).select_from(Embedding).where(Embedding.repo_id == live_id)
    )
    assert live_emb_res.scalar_one() == 1


def test_check_git_preconditions_clean():
    """Verify check_git_preconditions succeeds when repo is clean and up to date."""
    with patch("subprocess.run") as mock_run:
        # Mock status --porcelain: clean
        mock_run.side_effect = [
            MagicMock(stdout=""),  # git status --porcelain
            MagicMock(stdout="abcdef123456\n"),  # git rev-parse HEAD
            MagicMock(stdout="abcdef123456\n"),  # git rev-parse origin/main
            MagicMock(stdout="abcdef1\n"),  # git rev-parse --short HEAD
        ]
        short_sha = check_git_preconditions(skip_check=False)
        assert short_sha == "abcdef1"


def test_check_git_preconditions_dirty():
    """Verify check_git_preconditions aborts if git working tree is dirty."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=" M modified_file.py\n")
        with pytest.raises(RuntimeError, match="git working tree is dirty"):
            check_git_preconditions(skip_check=False)


def test_check_git_preconditions_branch_mismatch():
    """Verify check_git_preconditions aborts if local HEAD does not match origin/main."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(stdout=""),  # clean status
            MagicMock(stdout="111111111111\n"),  # local HEAD
            MagicMock(stdout="222222222222\n"),  # origin/main
        ]
        with pytest.raises(RuntimeError, match="local HEAD .* does not match origin/main"):
            check_git_preconditions(skip_check=False)
