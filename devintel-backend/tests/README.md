# DevIntel Backend - Test Suite

## Test Coverage Overview

This directory contains comprehensive tests for the DevIntel backend application.

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_api/               # API endpoint tests
│   ├── test_auth.py        # Authentication & OAuth tests
│   ├── test_repositories.py # Repository CRUD tests
│   ├── test_chat.py        # RAG chat endpoint tests
│   └── test_pr_review.py   # PR review tests (TODO)
├── test_services/          # Business logic tests
│   ├── test_indexing.py    # Repository indexing tests
│   ├── test_embedding.py   # Embedding generation tests (TODO)
│   └── test_chat.py        # Chat service tests (TODO)
├── test_repositories/      # Data layer tests (TODO)
└── integration/            # End-to-end tests (TODO)
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
pytest tests/test_api/test_auth.py -v

# Run specific test
pytest tests/test_api/test_auth.py::TestAuthEndpoints::test_health_check -v

# Run integration tests only
pytest -m integration

# Run excluding slow tests
pytest -m "not slow"
```

### Test Fixtures

Available fixtures (from `conftest.py`):

- `db_session` - Async database session (auto-rollback)
- `async_client` - Async HTTP client for API testing
- `test_client` - Synchronous test client
- `test_user` - Authenticated test user
- `test_user_token` - JWT token for test user
- `authenticated_client` - Pre-authenticated async client
- `test_repository` - Sample repository
- `indexed_repository` - Sample indexed repository
- `mock_openai_client` - Mocked OpenAI API
- `mock_github_client` - Mocked GitHub API
- `mock_redis_client` - Mocked Redis client

### Writing Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_example(authenticated_client: AsyncClient):
    \"\"\"Test description.\"\"\"
    response = await authenticated_client.get("/api/v1/endpoint")
    assert response.status_code == 200
```

### Coverage Goals

- **API Layer**: >90%
- **Services**: >85%
- **Repositories**: >95%
- **Overall**: >80%

### Current Status

- ✅ Test infrastructure setup
- ✅ Authentication tests (8 tests)
- ✅ Repository tests (12 tests)
- ✅ Chat tests (9 tests)
- ✅ Indexing service tests (10 tests)
- ⏳ Additional service tests (in progress)
- ⏳ Data layer tests (planned)
- ⏳ Integration tests (planned)

### TODO

1. Add embedding service tests
2. Add chat service tests  
3. Add data repository tests
4. Add integration tests for critical flows
5. Add performance tests
6. Achieve 80%+ coverage target
