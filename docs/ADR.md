# Architecture Decision Records

## ADR-001: JWT Refresh Token Strategy

**Date**: 2026-02-15  
**Status**: Accepted

### Context
Need secure authentication with minimal user friction while maintaining security best practices.

### Decision
- Access tokens: 15 minutes (short-lived)
- Refresh tokens: 7 days (long-lived)
- Refresh tokens stored in database
- Auto-refresh on 401 via frontend interceptor

### Consequences
✅ Reduced token theft window  
✅ Better security posture  
✅ Seamless user experience  
⚠️ Additional database queries  
⚠️ More complex frontend logic

---

## ADR-002: pgvector for Embeddings

**Date**: 2026-01-20  
**Status**: Accepted

### Context
Need efficient vector similarity search for RAG pipeline.

### Decision
Use pgvector PostgreSQL extension with IVFFlat indexes.

### Alternatives Considered
- Pinecone (vector database)
- Weaviate (vector database)
- FAISS (in-memory)

### Consequences
✅ Single database (simpler architecture)  
✅ ACID transactions  
✅ Cost-effective  
⚠️ Less performant than specialized vector DBs at scale  
⚠️ Requires PostgreSQL 11+

---

## ADR-003: Redis Connection Pooling

**Date**: 2026-02-15  
**Status**: Accepted

### Context
Multiple concurrent requests causing Redis connection exhaustion.

### Decision
Implement connection pooling with pool size of 10 connections.

### Consequences
✅ Better resource utilization  
✅ Prevents connection exhaustion  
✅ Improved performance  
⚠️ Slight complexity increase

---

## ADR-004: CSRF Protection Implementation

**Date**: 2026-02-15  
**Status**: Accepted

### Context
Need protection against CSRF attacks for state-changing operations.

### Decision
Token-based CSRF with `X-CSRF-Token` header validation.

### Alternatives Considered
- SameSite cookies only
- Double-submit cookies
- Origin header validation

### Consequences
✅ Industry standard approach  
✅ Works with SPAs  
✅ Compatible with API clients  
⚠️ Requires frontend integration  
⚠️ OAuth callbacks must be exempt

---

## ADR-005: Monorepo Structure

**Date**: 2026-01-15  
**Status**: Accepted

### Context
Backend and frontend closely coupled, need efficient development workflow.

### Decision
Monorepo with separate `devintel-backend` and `devintel-frontend` directories.

### Consequences
✅ Atomic commits across stack  
✅ Simplified dependency management  
✅ Easier code sharing  
⚠️ Larger repository size  
⚠️ More complex CI/CD

---

## Template for New ADRs

```markdown
## ADR-XXX: Title

**Date**: YYYY-MM-DD  
**Status**: [Proposed | Accepted | Rejected | Deprecated | Superseded]

### Context
What is the issue that we're seeing that is motivating this decision or change?

### Decision
What is the change that we're proposing and/or doing?

### Alternatives Considered
What other options were considered?

### Consequences
What becomes easier or more difficult to do because of this change?
Use ✅ for benefits, ⚠️ for drawbacks.
```
