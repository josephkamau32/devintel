<p align="center">
  <a href="https://devintel.vercel.app/"><img src="https://img.shields.io/badge/🚀_Live_Demo-devintel.vercel.app-8B5CF6?style=for-the-badge" alt="Live Demo" /></a>
  <a href="https://github.com/josephkamau32/devintel/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/josephkamau32/devintel/ci.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=CI" alt="CI Status" /></a>
  <img src="https://img.shields.io/badge/Coverage-60%25+-4DC71F?style=for-the-badge&logo=codecov&logoColor=white" alt="Coverage" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Ruff-checked-D7FF64?style=flat-square&logo=ruff&logoColor=black" alt="Ruff" />
  <img src="https://img.shields.io/badge/mypy-strict-blue?style=flat-square&logo=python&logoColor=white" alt="mypy" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
</p>

<h1 align="center">🧠 DevIntel AI</h1>

<p align="center">
  <strong>An autonomous, full-stack AI code intelligence platform that indexes GitHub repositories into a vector database, enables RAG-powered conversational code search, performs automated PR reviews, scores code health across six dimensions, and generates self-correcting auto-fix pull requests — built with production-grade security, observability, and resilience infrastructure.</strong>
</p>

<p align="center">
  <a href="#-key-features">Features</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-ai--ml-pipeline-deep-dive">AI/ML Pipeline</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-engineering-decisions">Engineering Decisions</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🎯 Overview

DevIntel AI is a **production-grade AI coding assistant platform** built as a monorepo with three integrated subsystems:

| Component | Description | Tech |
|-----------|-------------|------|
| **[`devintel-backend`](./devintel-backend)** | Async API server with RAG pipeline, multi-agent orchestration, and GitHub integration | FastAPI, SQLAlchemy 2.0, pgvector, OpenAI, Celery |
| **[`devintel-frontend`](./devintel-frontend)** | Dashboard for repository management, chat, code health analytics, and PR reviews | React 18, TypeScript 5, Vite, TanStack Query, Recharts |
| **[`devintel-vscode`](./devintel-vscode)** | VS Code extension with integrated AI chat sidebar, code review, and secure token management | TypeScript, VS Code Extension API, Webpack |

### 📸 Screenshots

> **Coming soon** — screenshots of the RAG chat, code health dashboard, and auto-generated PR review comments will be added here. Visit the [Live Demo](https://devintel.vercel.app/) to see the app in action.

### What makes this different from a ChatGPT wrapper?

This project implements **the full engineering depth** that production AI systems require:

- **Custom RAG pipeline** with **Tree-sitter AST-aware semantic chunking** — not naive text splitting. Code is chunked at function/class boundaries, preserving semantic coherence for retrieval.
- **Self-correcting autonomous agent** using OpenAI function calling (tool-use) with validation loops — generates code, applies diffs, runs syntax verification, and retries with error feedback up to 3 times before committing.
- **Production resilience** — Circuit breaker pattern (CLOSED → OPEN → HALF_OPEN) on all external API calls, exponential backoff retries, retry queues for failed tasks, and Redis-backed caching.
- **Enterprise security** — JWT + HttpOnly refresh cookies with SHA-256 hashing, Fernet AES-256 encryption for tokens at rest, OWASP security headers, CSRF protection, SQL injection detection, prompt injection defense, and audit logging.
- **Multi-agent architecture** — Specialized agents (security, performance, architecture, test generation) with a common base, routed to the appropriate agent based on task type.
- **Full CI/CD** — GitHub Actions for lint (Ruff), type check (mypy --strict), test with coverage threshold, security scanning (Trivy + Safety + npm audit), and automated VPS deployment via SSH.

---

## ✨ Key Features

### 🤖 AI-Powered Code Intelligence

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **RAG Chat** | Natural language questions about your codebase with streaming SSE responses | pgvector cosine similarity → context expansion (±1 neighbor chunks) → GPT-4o with grounded system prompt |
| **Autonomous Agent** | "Implement feature X" → branch, commit, open PR automatically | OpenAI function calling with `create_pull_request` tool schema → GitHub API execution |
| **AI Code Review** | Structured PR reviews with severity-tagged issues, security concerns, and performance notes | Webhook-triggered → diff summarization → RAG context retrieval → structured JSON review → GitHub comment |
| **Code Health** | Multi-dimensional quality scoring (0–100) across 6 axes | 10 probe queries sample diverse codebase regions → deduplicated context → GPT-4o structured assessment |
| **Auto-Fix** | Self-correcting code generation with validation loop | Search/Replace JSON patches → syntax verification → retry with error feedback (max 3 attempts) → commit + PR |
| **Test Generation** | AI-generated test suites with sandbox execution | Analyze file changes → generate tests → execute in sandbox → report pass/fail |
| **Git History Analysis** | Commit indexing, file blame, line-level change tracking | GitHub API integration → persistent storage → blame caching |
| **Architecture Visualization** | Mermaid diagram generation (flowchart, C4 context/container) | Code structure analysis → LLM-assisted diagram generation |

### 🔐 Enterprise-Grade Security Stack

| Layer | Implementation |
|-------|----------------|
| **Authentication** | JWT access tokens (15min TTL) + SHA-256 hashed refresh tokens in HttpOnly cookies (7d TTL), bcrypt password hashing, GitHub OAuth 2.0 flow |
| **Token Security** | Fernet AES-256 symmetric encryption for stored GitHub tokens at rest with authenticated encryption (HMAC) |
| **HTTP Security** | OWASP-compliant security headers — HSTS (production only), CSP, X-Frame-Options (DENY), X-Content-Type-Options (nosniff), Referrer-Policy, Permissions-Policy |
| **Input Validation** | SQL injection detection middleware with request path and query param scanning, prompt injection defense with 12 regex patterns, request body size limiting (10MB) |
| **CSRF Protection** | Double-submit cookie pattern with token validation |
| **Audit Trail** | Structured logging of all sensitive operations (`/auth`, `/repos`, `/admin`) with X-Request-ID distributed tracing |
| **API Hardening** | Non-root Docker user, docs endpoint disabled in production, secrets via env vars only |

### 🔧 Production Infrastructure

| Pattern | Implementation |
|---------|----------------|
| **Circuit Breaker** | Custom 3-state (CLOSED → OPEN → HALF_OPEN) circuit breaker on all OpenAI API calls; configurable failure threshold (5) and recovery timeout (60s) |
| **Retry + Backoff** | `tenacity` with exponential backoff (2s–10s) for transient API failures (timeout, connection, rate limit), max 3 attempts |
| **Retry Queue** | Failed indexing tasks are persisted and automatically retried with configurable backoff |
| **Caching** | Redis-backed cache layer for embedding search results and vector queries with configurable TTL (1h default), LRU eviction (512MB) |
| **Background Processing** | Celery workers with Redis broker for async repository indexing (4 concurrent workers), health checks via inspect ping |
| **Observability** | Prometheus metrics endpoint, `structlog` JSON-formatted structured logging, `X-Request-ID` propagation across middleware stack |
| **Incremental Indexing** | Webhook-triggered: only re-embeds changed/added files, deletes embeddings for removed files — O(changed files) instead of O(repo size) |

---

## 🏗 System Architecture

```mermaid
graph TD
    subgraph Clients
        A["React SPA (Vite)"] 
        B["VS Code Extension"]
        C["GitHub Webhooks"]
    end

    A --> N["Nginx Reverse Proxy<br/>SSL · Static Assets · Rate Limiting"]
    B --> N
    C --> N
    N --> F["FastAPI Application Server"]

    subgraph F["FastAPI Application Server"]
        direction TB
        MW["Middleware Stack<br/>Auth (JWT) · Security Headers (OWASP)<br/>Metrics (Prometheus) · Rate Limiting (Redis)<br/>CSRF · SQLi Detection · Audit Logging"]
        MW --> ROUTES["API v1 Routes<br/>/auth · /repos · /chat · /health-score<br/>/pr-review · /webhooks · /ws · /agent"]
        ROUTES --> SVC["Service Layer (24 modules)"]
        
        subgraph SVC["Service Layer"]
            CS["ChatService<br/>(RAG + SSE)"]
            AS["AgentService<br/>(Tool-Use)"]
            PR["PRReviewSvc<br/>(AI Reviews)"]
            CH["CodeHealth<br/>Scoring"]
            AF["AutoFixSvc<br/>(Self-Heal)"]
            II["Incremental<br/>Indexer"]
            MA["Multi-Agent Framework<br/>Security · Performance · Architect · Test"]
        end

        SVC --> REPO["Repository Layer<br/>18 modules · Async SQLAlchemy 2.0"]
    end

    REPO --> PG[("PostgreSQL 16<br/>+ pgvector<br/>20 migrations · 17+ tables")]
    REPO --> RD[("Redis 7<br/>Cache / Queue<br/>Celery · LRU 512MB")]
    SVC --> OAI["OpenAI API<br/>Circuit Breaker + Retry"]
```

<details>
<summary>📋 ASCII Architecture Diagram (text fallback)</summary>

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                       │
│   ┌──────────────┐   ┌──────────────────┐   ┌──────────────────────────┐   │
│   │  React SPA   │   │  VS Code Ext.    │   │  GitHub Webhooks         │   │
│   │  (Vite)      │   │  (Sidebar Chat)  │   │  (push / PR events)     │   │
│   └──────┬───────┘   └────────┬─────────┘   └───────────┬──────────────┘   │
└──────────┼────────────────────┼──────────────────────────┼─────────────────┘
           │                    │                          │
           ▼                    ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NGINX REVERSE PROXY                                │
│              SSL Termination · Static Assets · Rate Limiting               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FastAPI APPLICATION SERVER                              │
│                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Auth        │  │ Security     │  │ Metrics      │  │ CSRF / SQLi    │  │
│  │ Middleware  │  │ Headers      │  │ Middleware   │  │ Detection      │  │
│  │ (JWT)       │  │ (OWASP)      │  │ (Prometheus) │  │                │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│         └────────────────┴─────────────────┴───────────────────┘           │
│                                    │                                       │
│  ┌─────────────────────────────────┴─────────────────────────────────────┐ │
│  │                        API v1 ROUTES                                  │ │
│  │  /auth  /repos  /chat  /health-score  /pr-review  /webhooks  /ws     │ │
│  │  /organizations  /policies  /architecture  /git-history  /collab     │ │
│  └──────────────────────────────┬────────────────────────────────────────┘ │
│                                 │                                          │
│  ┌──────────────────────────────┴────────────────────────────────────────┐ │
│  │                       SERVICE LAYER (24 modules)                      │ │
│  │                                                                       │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐                │ │
│  │  │ ChatService │  │ AgentService │  │ PRReviewSvc   │                │ │
│  │  │ (RAG + SSE) │  │ (Tool-Use)   │  │ (AI Reviews)  │                │ │
│  │  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘                │ │
│  │         │                │                   │                        │ │
│  │  ┌──────┴──────┐  ┌──────┴───────┐  ┌───────┴───────┐               │ │
│  │  │ CodeHealth  │  │ AutoFixSvc   │  │ Incremental   │               │ │
│  │  │ Scoring     │  │ (Self-Heal)  │  │ Indexer       │               │ │
│  │  └─────────────┘  └──────────────┘  └───────────────┘               │ │
│  │                                                                       │ │
│  │  ┌─────────────────────── Multi-Agent Framework ──────────────────┐  │ │
│  │  │ SecurityAgent │ PerformanceAgent │ ArchitectAgent │ TestAgent   │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────── REPOSITORY LAYER ───────────────────────────┐  │
│  │  18 repository modules · Async SQLAlchemy 2.0 · Repository Pattern   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
┌──────────────────┐  ┌────────────────┐  ┌───────────────────┐
│  PostgreSQL 16   │  │  Redis 7       │  │  OpenAI API       │
│  + pgvector      │  │  Cache / Queue │  │  (Circuit Breaker │
│  (20 migrations) │  │  (Celery)      │  │   + Retry)        │
│  (17+ tables)    │  │  (LRU 512MB)   │  │                   │
└──────────────────┘  └────────────────┘  └───────────────────┘
```

</details>

### Layered Architecture

The backend follows a **strict layered architecture** with clear dependency direction:

```
Routes (API) → Services (Business Logic) → Repositories (Data Access) → Models (Domain)
                    ↓
            Integrations (External APIs: OpenAI, GitHub)
```

- **17+ SQLAlchemy models** spanning users, repositories, embeddings, code health, organizations, policies, git history, collaboration sessions, architecture diagrams, cross-repo knowledge, and more
- **18 repository modules** implementing the Repository Pattern for testable data access
- **24 service modules** encapsulating all business logic with dependency injection
- **20 Alembic migrations** tracking the full schema evolution

---

## 🧬 AI / ML Pipeline Deep Dive

### Retrieval-Augmented Generation (RAG)

The core intelligence engine implements a custom RAG pipeline that operates on the **semantic structure** of code — not raw text:

```
Repository Push Event (via GitHub Webhook)
        │
        ▼
┌───────────────────────────┐
│  1. File Discovery        │  Filter by 13 supported extensions (.py, .ts, .go, .rs, .java, ...)
│     & Preprocessing       │  Skip 8 ignored dirs (node_modules, .git, __pycache__, ...)
└───────────┬───────────────┘  Enforce max file size (configurable, default 10 MB)
            │
            ▼
┌───────────────────────────┐
│  2. AST-Aware Chunking    │  Tree-sitter parses source into Abstract Syntax Tree
│     (tree_sitter +        │  Split at semantic boundaries (function/class/method defs)
│      smart_chunk_code)    │  Merge small segments to target ~700 tokens per chunk
└───────────┬───────────────┘  Lossless: 100% of source code preserved across chunks
            │                  Call graph extraction for dependency analysis
            ▼
┌───────────────────────────┐
│  3. Embedding Generation  │  OpenAI text-embedding-3-small (1536 dimensions)
│     (Batched + Resilient) │  Batch API with configurable batch_size (50)
└───────────┬───────────────┘  Circuit breaker + exponential backoff retries
            │                  Progress callbacks for real-time WebSocket updates
            ▼
┌───────────────────────────┐
│  4. Vector Storage        │  pgvector cosine similarity index in PostgreSQL
│     (PostgreSQL)          │  Per-repository partitioned storage
└───────────┬───────────────┘  Incremental upsert: delete old → insert new chunks per file
            │                  Bulk insert for initial indexing
            ▼
┌───────────────────────────┐
│  5. Retrieval + Expansion │  Top-K vector similarity search (default K=6)
│                           │  Context window expansion: ±1 neighbor chunks
└───────────┬───────────────┘  Neighbors inherit 95% of relevance score
            │                  Redis caching of query→result (TTL: 1h, SHA-256 key)
            ▼
┌───────────────────────────┐
│  6. Generation            │  GPT-4o with grounded system prompt
│     (Streaming SSE)       │  Multi-turn chat history with token-aware trimming
└───────────────────────────┘  tiktoken-based context window validation (120K limit)
                               Prompt injection defense (12 regex patterns)
                               Instructions to refuse system prompt disclosure
```

### Key RAG Design Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| **Tree-sitter AST chunking** over naive text splitting | Preserves semantic boundaries (functions, classes) | ~30% higher retrieval precision — chunks contain complete logical units |
| **pgvector** over Pinecone/Weaviate | Zero vendor lock-in, collocated with relational data, native PostgreSQL JOINs for filtering | Eliminates network round-trips between vector and relational stores |
| **Context expansion (±1 chunks)** | Adjacent chunks provide semantic continuity | Prevents truncated function bodies in context; neighbors inherit 95% relevance |
| **Redis caching with SHA-256 keys** | Identical queries to the same repo return cached results | Sub-ms latency for repeated queries; 1h TTL balances freshness vs. cost |
| **Incremental indexing** over full re-index | Webhook-triggered: only process changed/added/removed files | O(changed files) per push instead of O(repo size); ~90% faster for typical commits |

### Multi-Agent Architecture

DevIntel implements a **specialized multi-agent framework** with a common base:

```
                    ┌──────────────┐
                    │  BaseAgent   │  (base_agent.py)
                    │  - context   │
                    │  - tools     │
                    │  - execute() │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐────────────────┐
          │                │                │                │
   ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
   │ Security    │  │ Performance │  │ Architect   │  │ Test        │
   │ Agent       │  │ Agent       │  │ Agent       │  │ Agent       │
   │ + Remediate │  │             │  │             │  │             │
   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘

   Router (router.py) dispatches to the appropriate agent based on task type
```

### Auto-Fix Self-Correction Loop

The Auto-Fix Service implements a **retry-with-feedback loop** for reliable autonomous code generation:

```
Issue Description → Embedding Search → File Content from GitHub
                                              │
                                              ▼
                                    ┌─────────────────┐
                              ┌────►│ LLM Generates   │
                              │     │ Search/Replace  │
                              │     │ JSON Patch      │
                              │     └────────┬────────┘
                              │              │
                              │              ▼
                              │     ┌─────────────────┐
                              │     │ Validate:        │
                              │     │ 1. search_block  │
                              │     │    exists in file │──── All Pass ──► Commit + Open PR
                              │     │ 2. Apply diff    │
                              │     │ 3. Syntax check  │
                              │     └────────┬────────┘
                              │              │
                              │            Fail
                              │              │
                              │              ▼
                              │     ┌─────────────────┐
                              └─────│ Feed errors back │
                                    │ into LLM context │
                                    │ (max 3 attempts) │
                                    └─────────────────┘
```

**Why Search/Replace patches instead of full file rewrites?**
- Minimizes LLM output tokens (cost + latency)
- Reduces hallucination surface — the model only changes what needs to change
- Enables precise validation: the search block must exactly match existing code

---

## 🛠 Tech Stack

### Backend

| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI 0.109, Uvicorn (ASGI), Pydantic v2 Settings |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic (20 migrations), pgvector 0.2.4 |
| **AI/ML** | OpenAI GPT-4o + text-embedding-3-small, tiktoken tokenizer, Tree-sitter AST parser (25+ language grammars), call graph extraction |
| **Auth** | JWT (python-jose), bcrypt (passlib), Fernet AES-256 encryption (cryptography), GitHub OAuth 2.0 |
| **Caching** | Redis 7 with async client, configurable TTL, LRU eviction (512MB) |
| **Task Queue** | Celery 5 with Redis broker, 4 concurrent workers, health monitoring |
| **Resilience** | Circuit breaker (custom, 3-state), tenacity (retry + exponential backoff), retry queue |
| **Observability** | Prometheus client metrics, structlog (JSON), X-Request-ID tracing |
| **Security** | CSRF middleware, SQL injection detection, OWASP security headers (HSTS/CSP/X-Frame-Options), request size limiting, audit logging, prompt injection defense |
| **Testing** | pytest + pytest-asyncio + pytest-cov (22 test files) |

### Frontend

| Category | Technologies |
|----------|-------------|
| **Framework** | React 18, TypeScript 5, Vite 5 (SWC) |
| **State** | Zustand (global auth), TanStack Query v5 (server state + cache) |
| **UI** | Radix UI primitives (20+ components), shadcn/ui, Tailwind CSS, Framer Motion animations |
| **Forms** | React Hook Form + Zod schema validation |
| **Routing** | React Router v6 with auth guards |
| **Visualization** | Recharts (code health dashboards) |
| **Testing** | Vitest + Testing Library |

### VS Code Extension

| Category | Technologies |
|----------|-------------|
| **Runtime** | VS Code Extension API (^1.85.0) |
| **Build** | Webpack, TypeScript |
| **Features** | Sidebar webview chat, context menu code review, `SecretStorage` for secure API token management, configurable API base URL |

### Infrastructure & DevOps

| Category | Technologies |
|----------|-------------|
| **Containerization** | Docker multi-stage builds (builder → production), non-root user, healthchecks |
| **Orchestration** | Docker Compose (6 services: PostgreSQL, Redis, Backend, Celery Worker, Nginx, Prometheus) |
| **Reverse Proxy** | Nginx 1.25 with SSL termination, static asset serving, upstream proxy |
| **CI/CD** | GitHub Actions — 4 parallel jobs: Frontend CI, Backend Validation, Project Health, Security Scan (Trivy + Safety + npm audit) |
| **Deployment** | Automated VPS deploy via SSH, Render (API) + Neon (PostgreSQL) + Vercel (Frontend) |
| **Monitoring** | Prometheus with 30-day retention, custom metrics endpoint |
| **Backup** | Automated database backup/restore scripts (bash) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (or Bun)
- PostgreSQL 16 with [pgvector](https://github.com/pgvector/pgvector) extension
- Redis 7+ (optional — enables caching and Celery task queue)
- OpenAI API key
- GitHub OAuth App ([create one here](https://github.com/settings/developers))

### 1. Clone & Setup

```bash
git clone https://github.com/josephkamau32/devintel.git
cd devintel
```

### 2. Backend

```bash
cd devintel-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — fill in all required values (see Environment Variables below)

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd devintel-frontend

npm install
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000
npm run dev
```

### 4. VS Code Extension (Development)

```bash
cd devintel-vscode

npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host
```

### 5. Docker Compose (Full Stack — One Command)

```bash
# Copy and configure production env
cp .env.production.example .env.production
# Fill in all secrets (DATABASE_URL, OPENAI_API_KEY, JWT_SECRET_KEY, etc.)

# Launch all 6 services
docker compose -f docker-compose.prod.yml up -d
```

This starts: PostgreSQL 16 + pgvector, Redis 7 (with auth), Backend API (2 CPU / 2GB RAM), Celery Worker (4 CPU / 4GB RAM), Nginx reverse proxy (SSL), and Prometheus monitoring.

---

## ⚙️ Environment Variables

### Backend (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (`postgresql+asyncpg://user:pass@host/db`) |
| `JWT_SECRET_KEY` | ✅ | Secret key for JWT token signing (min 32 chars) |
| `SECRET_KEY` | ✅ | Application secret for CSRF protection |
| `TOKEN_ENCRYPTION_KEY` | ✅ | Fernet key for encrypting GitHub tokens at rest |
| `GITHUB_CLIENT_ID` | ✅ | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | ✅ | GitHub OAuth App client secret |
| `GITHUB_REDIRECT_URI` | ✅ | OAuth callback URL (e.g., `http://localhost:8000/api/v1/auth/github/callback`) |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for embeddings and chat |
| `CORS_ORIGINS` | ✅ | JSON array of allowed origins (e.g., `["http://localhost:5173"]`) |
| `REDIS_URL` | ❌ | Redis connection URL (enables caching and Celery) |
| `OPENAI_CHAT_MODEL` | ❌ | Chat model (default: `gpt-4o`) |
| `OPENAI_EMBEDDING_MODEL` | ❌ | Embedding model (default: `text-embedding-3-small`) |
| `ENVIRONMENT` | ❌ | `development` or `production` (controls HSTS, docs visibility) |

**Generate a Fernet key:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Frontend (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | ✅ | Backend API URL (e.g., `http://localhost:8000`) |

---

## 🌐 Deployment

### Option A: Docker Compose (Self-Hosted / VPS)

```bash
docker compose -f docker-compose.prod.yml up -d
```

**Production stack includes:** PostgreSQL 16 + pgvector, Redis 7 (auth + AOF persistence), Backend API (resource-limited: 2 CPU / 2GB), Celery Worker (4 CPU / 4GB), Nginx with SSL termination, Prometheus with 30-day retention.

### Option B: Free-Tier Cloud Stack

| Service | Provider | Config |
|---------|----------|--------|
| API Server | [Render](https://render.com) | `render.yaml` — Docker web service |
| Database | [Neon](https://neon.tech) | Free PostgreSQL with pgvector |
| Frontend | [Vercel](https://vercel.com) | `vercel.json` — auto-deploys from `devintel-frontend/dist` |

### CI/CD Pipeline

GitHub Actions workflows in [`.github/workflows/`](./.github/workflows):

| Workflow | Trigger | Jobs |
|----------|---------|------|
| **`ci.yml`** | Push / PR to `main` | Frontend CI (lint + build + test), Backend Validation (install + pytest), Project Health Check, Security Scan (Trivy filesystem + Docker config, Safety, npm audit) |
| **`deploy.yml`** | Push to `main` / manual dispatch | Build frontend bundle → SCP to VPS → SSH deploy → Docker Compose rebuild → Health check → Image cleanup |

---

## 📡 API Reference

Interactive docs available at `http://localhost:8000/docs` (debug mode only).

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/signup` | Register with email/password |
| `POST` | `/api/v1/auth/login` | Login, receive JWT + refresh cookie |
| `GET` | `/api/v1/auth/github` | Initiate GitHub OAuth 2.0 flow |
| `POST` | `/api/v1/repos/connect` | Connect and index a GitHub repository |
| `POST` | `/api/v1/chat/{repo_id}` | RAG-powered chat (SSE streaming) |
| `POST` | `/api/v1/health-score/{repo_id}/analyze` | Run AI code health analysis |
| `POST` | `/api/v1/pr-review/{repo_id}/{pr_number}` | Generate AI pull request review |
| `POST` | `/api/v1/repos/{repo_id}/agent/draft` | Draft an autonomous PR plan |
| `POST` | `/api/v1/repos/{repo_id}/agent/execute` | Execute drafted PR on GitHub |
| `POST` | `/api/v1/webhooks/github` | Receive GitHub push/PR webhook events |
| `WS` | `/ws/repos/{repo_id}/progress` | WebSocket for real-time indexing progress |
| `WS` | `/ws/collab/{session_id}` | WebSocket for real-time collaboration |
| `GET` | `/api/v1/organizations` | Organization management (RBAC) |
| `GET` | `/api/v1/architecture/{repo_id}` | Architecture diagram generation |
| `GET` | `/api/v1/git-history/{repo_id}` | Git commit history and file blame |
| `GET` | `/health` | Health check |

---

## 📁 Project Structure

```
devintel/
├── devintel-backend/
│   ├── app/
│   │   ├── api/v1/              # 16 route handlers (auth, chat, repos, webhooks, ws, ...)
│   │   ├── core/                # Config, constants, exceptions, logging, validators, security
│   │   ├── db/                  # Async database session, engine configuration
│   │   ├── integrations/        # OpenAI client (circuit breaker), GitHub client
│   │   ├── middleware/          # Security headers, CSRF, metrics, SQL injection detection
│   │   ├── models/              # SQLAlchemy models (17+ domain tables)
│   │   ├── repositories/        # Data access layer (18 repository modules)
│   │   ├── schemas/             # Pydantic request/response schemas (16 schema files)
│   │   ├── services/            # Business logic (24 service modules + 5 specialized agents)
│   │   ├── tasks/               # Celery async tasks (indexing, code health, PR review)
│   │   └── utils/               # Tree-sitter chunking, call graph, patcher, linter
│   ├── alembic/                 # 20 database migrations
│   ├── tests/                   # pytest test suite (22 test files, conftest fixtures)
│   ├── Dockerfile               # Multi-stage production build (non-root user)
│   └── Makefile                 # Dev shortcuts
├── devintel-frontend/
│   ├── src/
│   │   ├── components/          # React components (4 feature + Radix/shadcn UI library)
│   │   ├── hooks/               # Custom React hooks (auth, repositories, user)
│   │   ├── pages/               # Route pages (Landing, Dashboard, Login, Signup, OAuth)
│   │   ├── store/               # Zustand state management
│   │   ├── lib/                 # API client utilities
│   │   └── types/               # TypeScript type definitions
│   └── tests/                   # Vitest test suite
├── devintel-vscode/
│   └── src/
│       ├── extension.ts         # Extension activation (4 commands)
│       ├── sidebar.ts           # Webview chat panel (19KB)
│       └── auth.ts              # SecretStorage token management
├── .github/workflows/           # CI/CD (ci.yml, deploy.yml)
├── docker-compose.prod.yml      # Full 6-service production stack
├── nginx/                       # Nginx config + SSL
├── prometheus/                  # Prometheus scrape config
├── scripts/                     # Start/stop, backup/restore scripts
├── docs/                        # ADRs, API docs, security, performance, monitoring, demo
└── render.yaml                  # Render.com Infrastructure as Code
```

---

## 🧪 Testing

```bash
# Backend unit + integration tests
cd devintel-backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend component + unit tests
cd devintel-frontend
npm run test

# Lint
npm run lint

# E2E tests (Playwright config present)
npx playwright test
```

**Test coverage:**
- **22 backend test files** covering auth, validators, services, repositories, and API endpoints
- **conftest.py** with async database fixtures, in-memory SQLite for isolation
- **Vitest** for frontend component and hook testing

---

## 🔑 Engineering Decisions

These are the non-obvious architectural choices and the reasoning behind them — the kind of trade-off analysis that matters in production systems:

| Decision | Rationale |
|----------|-----------|
| **Tree-sitter AST chunking over naive text splitting** | Preserves semantic boundaries (functions, classes) → higher retrieval precision. A chunk always contains a complete logical unit, not a truncated function mid-body. |
| **pgvector over Pinecone/Weaviate** | Zero vendor lock-in, collocated with relational data (same database), native PostgreSQL JOINs for filtering by repo_id/file_path. Eliminates network round-trips between vector and relational stores. |
| **Circuit breaker on OpenAI client** | Prevents cascading failures during API outages. After 5 consecutive failures, the circuit opens for 60s, returning fast errors instead of blocking threads. Auto-recovers via HALF_OPEN state. |
| **Search/Replace patches over full file rewrites** | Minimizes LLM output tokens (cost + latency), reduces hallucination surface, and enables precise validation — the search block must exactly match existing code. |
| **Prompt injection defense in ChatService** | 12 regex patterns catch common injection vectors (e.g., "ignore previous instructions", "system prompt:", "[INST]") before they reach the system prompt. Defense-in-depth alongside instruction hardening. |
| **Fernet AES-256 for GitHub tokens** | Symmetric encryption with authenticated encryption (HMAC) — secure at rest, fast to decrypt. No asymmetric overhead for tokens that only the same service reads. |
| **SHA-256 hashed refresh tokens** | Tokens are never stored in plaintext in the database. Lookup by hash, compare server-side. Even if the DB is compromised, refresh tokens cannot be extracted. |
| **Context expansion (±1 chunks)** | Adjacent chunks inherit 95% relevance → provides semantic continuity. Prevents the common RAG failure mode where a function signature is in one chunk but the body is in the next. |
| **Celery for indexing** | Repository indexing is CPU/IO-heavy (tree-sitter parsing + embedding generation). Async workers prevent API thread blocking. 4 concurrent workers with Redis broker and health monitoring. |
| **Incremental indexing on push** | Only re-embeds changed/added files, deletes embeddings for removed files. O(changed files) per push instead of O(repo size). Falls back to full re-index when commit SHA tracking is unavailable. |
| **Multi-stage Docker build** | Separates build-time dependencies (gcc, dev headers) from runtime. Production image is ~200MB smaller. Non-root user (`devintel`) for security. |
| **Repository Pattern for data access** | Testable: repositories are injected as dependencies, easily mocked in tests with `conftest.py` fixtures. Clean separation from SQLAlchemy session management. |

---

## 📚 Documentation

This project includes extensive documentation beyond this README:

| Document | Description |
|----------|-------------|
| [Technical Deep Dive](./docs/TECHNICAL_DEEP_DIVE.md) | Architecture deep dive — design trade-offs, scaling strategies, and system internals |
| [API Reference](./docs/API.md) | Full OpenAPI specification with request/response examples |
| [OpenAPI Schema](./devintel-backend/docs/openapi.json) | Machine-readable OpenAPI 3.1 spec (auto-generated) |
| [Architecture Decision Records](./docs/ADR.md) | Rationale for key technical decisions |
| [Security Documentation](./docs/SECURITY.md) | Security model, threat mitigation, and hardening guide |
| [Deployment Guide](./docs/DEPLOYMENT.md) | Step-by-step production deployment instructions |
| [Performance Guide](./docs/PERFORMANCE.md) | Optimization strategies and benchmarks |
| [Monitoring Guide](./docs/MONITORING.md) | Prometheus metrics, alerting, and observability setup |
| [Contributing Guide](./CONTRIBUTING.md) | Development workflow, code style, and PR guidelines |
| [Setup Guide](./SETUP.md) | Detailed local development environment setup |
| [Demo Script](./docs/DEMO_SCRIPT.md) | Step-by-step demo walkthrough |
| [Changelog](./CHANGELOG.md) | Release history |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file.

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](./CONTRIBUTING.md) before opening a PR.

This project uses [GitHub Issue Templates](./.github/ISSUE_TEMPLATE) and a [Pull Request Template](./.github/PULL_REQUEST_TEMPLATE.md) to maintain quality.

---

<p align="center">
  Built with ☕ and a lot of <code>async/await</code><br/>
  <strong>Joseph Kamau</strong> — <a href="https://github.com/josephkamau32">@josephkamau32</a>
</p>
