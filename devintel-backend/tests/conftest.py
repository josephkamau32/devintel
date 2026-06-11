"""Pytest configuration and shared fixtures for testing."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Load environment variables from .env file
load_dotenv()

from app.core.config import settings

settings.database_url = "sqlite+aiosqlite:///:memory:"

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.repository import Repository
from app.models.user import User

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session maker
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)




@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Automatically rolls back after test completes.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for API testing.
    Automatically injects test database session.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client() -> TestClient:
    """Create a synchronous test client for simple tests."""
    return TestClient(app)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        github_id="test_github_123",
        email="test@example.com",
        name="Test User",
        avatar_url="https://avatars.githubusercontent.com/u/123",
        github_access_token_encrypted="test_token_abc123",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_token(test_user: User) -> str:
    """Create a JWT token for the test user."""
    return create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )


@pytest_asyncio.fixture
async def authenticated_client(
    async_client: AsyncClient, test_user_token: str
) -> AsyncClient:
    """Create an authenticated async client with JWT token."""
    async_client.headers["Authorization"] = f"Bearer {test_user_token}"
    return async_client


@pytest_asyncio.fixture
async def auth_headers(test_user_token: str) -> dict:
    """Create authentication headers for the test user."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest_asyncio.fixture
async def active_user(db_session: AsyncSession) -> User:
    """Create a second (active) test user in the database."""
    user = User(
        github_id="active_github_456",
        email="active@example.com",
        name="Active User",
        username="activeuser",
        avatar_url="https://avatars.githubusercontent.com/u/456",
        github_access_token_encrypted="active_token_xyz789",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def active_user_token(active_user: User) -> str:
    """Create a JWT token for the active user."""
    return create_access_token(
        data={"sub": str(active_user.id), "email": active_user.email}
    )


@pytest_asyncio.fixture
async def active_user_auth_headers(active_user_token: str) -> dict:
    """Create authentication headers for the active (second) test user."""
    return {"Authorization": f"Bearer {active_user_token}"}


@pytest_asyncio.fixture
async def test_repository(db_session: AsyncSession, test_user: User) -> Repository:
    """Create a test repository in the database."""
    repository = Repository(
        user_id=test_user.id,
        full_name="test-user/test-repo",
        repo_name="test-repo",
        url="https://github.com/test-user/test-repo.git",
        indexed_status=False,
        indexing_progress=0,
    )
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    return repository


@pytest_asyncio.fixture
async def indexed_repository(
    db_session: AsyncSession, test_repository: Repository
) -> Repository:
    """Create a test repository that has been indexed."""
    test_repository.indexed_status = True
    test_repository.indexing_progress = 100
    await db_session.commit()
    await db_session.refresh(test_repository)
    return test_repository


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls."""
    mock = MagicMock()

    # Mock embeddings
    mock.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    )

    # Mock chat completions
    async def mock_chat_stream():
        """Mock streaming chat response."""
        chunks = ["Hello", " from", " mocked", " AI!"]
        for chunk in chunks:
            yield MagicMock(
                choices=[
                    MagicMock(
                        delta=MagicMock(content=chunk, role="assistant"),
                        finish_reason=None,
                    )
                ]
            )

    mock.chat.completions.create.return_value = mock_chat_stream()

    return mock


@pytest.fixture
def mock_github_client():
    """Mock GitHub API client for testing."""
    mock = MagicMock()

    # Mock user data - get_user is synchronous in PyGithub, but our wrapper might be async?
    # Wait, the code uses `await github_client.get_user_info()`.
    # Our GitHubClient WRAPPER has async methods.
    # The test patches "app.api.v1.auth.GitHubClient".
    # The return_value of that patch is this mock.
    # So this mock represents the GitHubClient INSTANCE.
    # Its methods (get_user_info) should be async.

    mock.get_user_info = AsyncMock(return_value={
        "github_id": "123",
        "login": "testuser",
        "name": "Test User",
        "email": "test@example.com",
        "avatar_url": "https://avatars.githubusercontent.com/u/123",
    })

    mock.get_user_repositories = AsyncMock(return_value=[
        {
            "repo_name": "repo1",
            "full_name": "testuser/repo1",
            "url": "https://github.com/testuser/repo1",
            "clone_url": "https://github.com/testuser/repo1.git",
            "stars": 10,
            "language": "Python",
            "private": False,
            "description": "Test Repo 1"
        },
        {
            "repo_name": "repo2",
            "full_name": "testuser/repo2",
            "url": "https://github.com/testuser/repo2",
            "clone_url": "https://github.com/testuser/repo2.git",
            "stars": 5,
            "language": "JavaScript",
            "private": True,
            "description": "Test Repo 2"
        },
    ])

    return mock


@pytest.fixture(autouse=True)
async def disable_csrf():
    """Disable CSRF protection for tests."""
    async def bypass_csrf(request, call_next):
        return await call_next(request)

    with patch("app.middleware.csrf.CSRFMiddleware.dispatch", side_effect=bypass_csrf):
        yield


@pytest.fixture(autouse=True)
async def mock_redis():
    """Mock Redis / ensure cache uses in-memory backend for tests."""
    from app.services.cache import cache
    # Force in-memory mode for tests (no Redis needed)
    if cache._mem is None:
        from app.services.cache import _InMemoryCache
        cache._redis = None
        cache._mem = _InMemoryCache()
    yield cache


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing caching."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    return mock


@pytest.fixture
def sample_code_chunk():
    """Sample code chunk for testing."""
    return """
def calculate_sum(a: int, b: int) -> int:
    \"\"\"Calculate the sum of two numbers.\"\"\"
    return a + b

def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers.\"\"\"
    return a * b
"""


@pytest.fixture
def sample_embedding():
    """Sample embedding vector for testing."""
    # Return a simple 1536-dimensional vector (OpenAI text-embedding-3-small)
    return [0.01] * 1536


@pytest_asyncio.fixture
async def cleanup_db(db_session: AsyncSession):
    """Fixture to clean up database after tests."""
    yield
    # Cleanup happens automatically via db_session rollback


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "unit: mark test as unit test")


# Pytest asyncio mode
pytest_plugins = ("pytest_asyncio",)
