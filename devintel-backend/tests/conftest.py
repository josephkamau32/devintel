import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models.user import User
from app.models.repository import Repository
from app.core.security import create_access_token, hash_password

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


def pytest_ignore_collect(collection_path, config):
    if collection_path.is_dir():
        return collection_path.name not in {
            "tests", "test_api", "test_integration",
            "test_repositories", "test_services", "__pycache__"
        }
    return not collection_path.name.startswith("test_") or not collection_path.name.endswith(".py")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset in-memory rate limiting store before and after each test."""
    from app.middleware.rate_limit import reset_in_memory_rate_limit_store
    reset_in_memory_rate_limit_store()
    yield
    reset_in_memory_rate_limit_store()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Alias: some tests use 'async_client', others use 'client'
@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        github_token_encrypted="some_encrypted_token_here",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_user_token(test_user: User) -> str:
    """Create a valid JWT access token for the test user."""
    token = create_access_token(test_user.id)
    return token


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, test_user_token: str) -> AsyncClient:
    """Return an authenticated test client."""
    client.headers = {"Authorization": f"Bearer {test_user_token}"}
    return client


@pytest_asyncio.fixture(scope="function")
async def test_repository(db_session: AsyncSession, test_user: User) -> Repository:
    """Create a test repository in the database."""
    repo = Repository(
        user_id=test_user.id,
        repo_name="testrepo",
        full_name="testowner/testrepo",
        description="Test repository",
        url="https://github.com/testowner/testrepo",
        default_branch="main",
    )
    db_session.add(repo)
    await db_session.flush()
    await db_session.refresh(repo)
    return repo


@pytest_asyncio.fixture(scope="function")
async def indexed_repository(db_session: AsyncSession, test_user: User) -> Repository:
    """Create a test repository that is fully indexed in the database."""
    from app.models.repository import IndexingStatus
    repo = Repository(
        user_id=test_user.id,
        repo_name="indexedrepo",
        full_name="testowner/indexedrepo",
        description="Indexed test repository",
        url="https://github.com/testowner/indexedrepo",
        default_branch="main",
        indexing_status=IndexingStatus.COMPLETE
    )
    db_session.add(repo)
    await db_session.flush()
    await db_session.refresh(repo)
    return repo


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user_token: str) -> dict:
    """Return auth headers for the test user."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest_asyncio.fixture(scope="function")
async def active_user(db_session: AsyncSession) -> User:
    """Create a secondary active test user in the database."""
    user = User(
        email="active@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Active User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def active_user_token(active_user: User) -> str:
    """Create a valid JWT access token for the active user."""
    return create_access_token(active_user.id)


@pytest_asyncio.fixture(scope="function")
async def active_user_auth_headers(active_user_token: str) -> dict:
    """Return auth headers for the active user."""
    return {"Authorization": f"Bearer {active_user_token}"}

