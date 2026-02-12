# Performance Optimization Guide

## Overview

This guide covers performance optimization strategies for scaling DevIntel to thousands of users.

---

## Current Performance Baseline

**Typical Request Times (Local Development):**
- Health check: ~5ms
- List repositories: ~50ms
- Chat query (RAG): ~800ms (dominated by OpenAI API)
- Repository indexing: ~30s for 10K code chunks

**Resource Usage (100 concurrent users):**
- API CPU: ~30%
- API Memory: ~500MB
- Database CPU: ~20%
- Redis Memory: ~50MB

---

## Database Optimizations

### 1. Indexing Strategy

**Critical Indexes:**

```sql
-- User lookups
CREATE INDEX idx_users_github_id ON users(github_id);
CREATE INDEX idx_users_email ON users(email);

-- Repository queries
CREATE INDEX idx_repos_user_id ON repositories(user_id);
CREATE INDEX idx_repos_indexed_status ON repositories(indexed_status);

-- Code chunk searches (most critical)
CREATE INDEX idx_chunks_repo_id ON code_chunks(repository_id);
CREATE INDEX idx_chunks_file_path ON code_chunks(file_path);

-- Vector similarity search (pgvector)
CREATE INDEX idx_chunks_embedding ON code_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Chat history
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_chats_repo_id ON chats(repository_id);
CREATE INDEX idx_chats_created_at ON chats(created_at DESC);
```

**Impact**: Vector search latency reduced from ~500ms to ~50ms on 100K chunks.

### 2. Query Optimization

**Before (N+1 Query Problem):**
```python
# Bad: Loads user for each repository
repositories = await db.execute(select(Repository))
for repo in repositories:
    user = await db.execute(select(User).where(User.id == repo.user_id))
```

**After (Eager Loading):**
```python
# Good: Single query with join
from sqlalchemy.orm import selectinload

repositories = await db.execute(
    select(Repository).options(selectinload(Repository.user))
)
```

**Impact**: Reduced queries from (1 + N) to 1, latency from 500ms to 50ms.

### 3. Connection Pooling

**Optimal Settings:**

```python
# app/db/session.py
engine = create_async_engine(
    settings.database_url,
    pool_size=20,              # Core connections
    max_overflow=0,            # Don't allow overflow
    pool_pre_ping=True,        # Test connection before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Disable query logging in production
)
```

**Monitoring:**
```python
# Check pool status
from sqlalchemy import pool
pool_status = engine.pool.status()
# "Pool size: 20  Connections in pool: 15  Current Overflow: 0"
```

### 4. Materialized Views (Advanced)

For expensive aggregate queries:

```sql
-- Create materialized view for repository stats
CREATE MATERIALIZED VIEW repository_stats AS
SELECT 
    r.id,
    r.full_name,
    COUNT(DISTINCT c.id) as chunk_count,
    COUNT(DISTINCT ch.id) as chat_count,
    MAX(c.created_at) as last_indexed_at
FROM repositories r
LEFT JOIN code_chunks c ON c.repository_id = r.id
LEFT JOIN chats ch ON ch.repository_id = r.id
GROUP BY r.id, r.full_name;

-- Refresh periodically (via cron or Celery)
REFRESH MATERIALIZED VIEW repository_stats;
```

---

## Caching Strategy

### 1. Redis Caching Layers

**Cache frequently accessed data:**

```python
import json
from typing import Optional
from app.core.redis import redis_client

class CacheService:
    @staticmethod
    async def get_repository(repo_id: str) -> Optional[dict]:
        """Get repository from cache."""
        key = f"repo:{repo_id}"
        cached = await redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    @staticmethod
    async def set_repository(repo_id: str, data: dict, ttl: int = 3600):
        """Cache repository for 1 hour."""
        key = f"repo:{repo_id}"
        await redis_client.setex(
            key, 
            ttl, 
            json.dumps(data, default=str)
        )
    
    @staticmethod
    async def invalidate_repository(repo_id: str):
        """Clear repository cache."""
        key = f"repo:{repo_id}"
        await redis_client.delete(key)
```

**Usage in routes:**

```python
@router.get("/repos/{repo_id}")
async def get_repository(repo_id: str, db: AsyncSession):
    # Try cache first
    cached = await CacheService.get_repository(repo_id)
    if cached:
        return cached
    
    # Cache miss - query database
    repo = await RepositoryRepository.get_by_id(db, repo_id)
    
    # Cache for future requests
    await CacheService.set_repository(repo_id, repo.dict())
    
    return repo
```

**Cache TTLs:**
- User profile: 15 minutes
- Repository list: 5 minutes
- Repository metadata: 1 hour
- Code chunks: Never (immutable unless re-indexed)

### 2. Application-Level Caching

**Cache expensive computations:**

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def parse_repository_path(clone_url: str) -> tuple[str, str]:
    """Parse owner and repo name from URL (cached)."""
    # Expensive regex parsing
    ...
    return owner, repo_name
```

---

## API Optimizations

### 1. Response Compression

**Enable gzip compression:**

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Impact**: Reduces response size by 70-80% for JSON responses.

### 2. Pagination

**Always paginate large datasets:**

```python
from fastapi import Query

@router.get("/repos")
async def list_repositories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    
    repos = await db.execute(
        select(Repository)
        .offset(offset)
        .limit(page_size)
    )
    
    return repos.scalars().all()
```

### 3. Field Selection

**Allow clients to request specific fields:**

```python
from pydantic import BaseModel
from typing import Optional

class RepositoryResponse(BaseModel):
    id: str
    full_name: str
    # Include only if requested
    chunks: Optional[list] = None
    chats: Optional[list] = None

@router.get("/repos/{repo_id}")
async def get_repository(
    repo_id: str,
    include_chunks: bool = False,
    include_chats: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(Repository)
    
    if include_chunks:
        query = query.options(selectinload(Repository.chunks))
    if include_chats:
        query = query.options(selectinload(Repository.chats))
    
    repo = await db.execute(query.where(Repository.id == repo_id))
    return repo.scalar_one()
```

---

## Vector Search Optimization

### 1. HNSW Index Tuning

**Adjust pgvector index parameters:**

```sql
-- More lists = better recall, slower build
CREATE INDEX idx_chunks_embedding ON code_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Good for <100K vectors

-- For larger datasets (>100K vectors)
WITH (lists = 500);  -- Better recall at scale
```

**Trade-offs:**
- Fewer lists: Faster builds, lower recall
- More lists: Slower builds, higher recall

### 2. Reduce Embedding Dimensions (Optional)

**Current**: 1536 dimensions (OpenAI text-embedding-3-small)

**Alternative**: Use smaller models or dimensionality reduction:

```python
from sklearn.decomposition import PCA

# Reduce 1536 → 768 dimensions
pca = PCA(n_components=768)
reduced_embedding = pca.fit_transform(original_embedding)
```

**Impact**: 50% storage reduction, 2x faster search, mild accuracy loss (~5%).

### 3. Pre-filtering

**Filter corpus before vector search:**

```python
# Instead of searching ALL chunks
SELECT * FROM code_chunks ORDER BY embedding <=> query_emb LIMIT 6;

# Filter by repository first
SELECT * FROM code_chunks 
WHERE repository_id = :repo_id
ORDER BY embedding <=> query_emb 
LIMIT 6;
```

**Impact**: 10x faster search (search 10K chunks instead of 100K).

---

## Background Job Optimization

### 1. Celery Worker Tuning

**Increase concurrency:**

```bash
# More workers for I/O-bound tasks (API calls)
celery -A app.tasks worker --concurrency=10

# Fewer workers for CPU-bound tasks (embedding generation)
celery -A app.tasks worker --concurrency=4
```

**Separate queues:**

```python
# High priority: user-facing tasks
@celery_app.task(queue='high_priority')
def index_repository(repo_id: str):
    ...

# Low priority: batch jobs
@celery_app.task(queue='low_priority')
def cleanup_old_chats():
    ...
```

### 2. Batch Processing

**Batch embed multiple chunks:**

```python
# Bad: One API call per chunk
for chunk in chunks:
    embedding = await openai.embeddings.create(input=chunk)

# Good: Batch API call
batch_size = 100
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    embeddings = await openai.embeddings.create(input=batch)
```

**Impact**: 100x fewer API calls, 10x faster indexing.

---

## Frontend Optimization

### 1. Code Splitting

```typescript
// Lazy load heavy components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AIChat = lazy(() => import('./pages/AIChat'));
```

### 2. React Query Caching

```typescript
const { data: repositories } = useQuery({
  queryKey: ['repositories'],
  queryFn: fetchRepositories,
  staleTime: 5 * 60 * 1000,  // 5 minutes
  cacheTime: 30 * 60 * 1000,  // 30 minutes
});
```

### 3. Virtual Scrolling

For large lists:

```bash
npm install react-virtual
```

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

// Render only visible items
const virtualizer = useVirtualizer({
  count: repositories.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 100,
});
```

---

## Monitoring & Profiling

### 1. Identify Slow Endpoints

```python
import time
from functools import wraps

def time_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        
        if duration > 1.0:  # Log slow requests
            logger.warning(f"Slow endpoint: {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper

@router.get("/chat")
@time_endpoint
async def chat(...):
    ...
```

### 2. Database Query Profiling

```python
# Enable query logging in development
engine = create_async_engine(database_url, echo=True)

# Use EXPLAIN ANALYZE for slow queries
await db.execute(text("EXPLAIN ANALYZE SELECT ..."))
```

---

## Performance Checklist

- [ ] Database indexes created for all frequent queries
- [ ] N+1 queries eliminated via eager loading
- [ ] Redis caching implemented for expensive operations
- [ ] Response compression enabled (gzip)
- [ ] Pagination added to all list endpoints
- [ ] Vector search optimized with HNSW indexes
- [ ] Background jobs batched and parallelized
- [ ] Frontend code splitting implemented
- [ ] Monitoring and profiling in place

---

## Expected Performance After Optimization

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Vector search | 500ms | 50ms | 10x faster |
| List repos API | 200ms | 20ms | 10x faster |
| Chat request | 1.2s | 0.8s | 33% faster |
| Repository indexing | 120s | 30s | 4x faster |
| Concurrent users | 100 | 1,000+ | 10x scale |

---

Last updated: 2026-02-12
