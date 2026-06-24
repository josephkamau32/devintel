<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
</p>

<h1 align="center">🧠 DevIntel AI</h1>

<p align="center">
  <strong>An autonomous AI-powered code intelligence platform that indexes your repositories, answers questions with RAG, reviews pull requests, scores code health, and generates auto-fix PRs — all with production-grade security, observability, and deployment infrastructure.</strong>
</p>

<p align="center">
  <a href="#-key-features">Features</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-ai--ml-pipeline">AI/ML Pipeline</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🎯 Overview

DevIntel AI is a **full-stack AI coding assistant platform** built as a monorepo with three integrated subsystems:

| Component | Description | Tech |
|-----------|-------------|------|
| **[`devintel-backend`](./devintel-backend)** | Async API server with RAG pipeline, agent orchestration, and GitHub integration | FastAPI, SQLAlchemy, pgvector, OpenAI |
| **[`devintel-frontend`](./devintel-frontend)** | Dashboard for repository management, chat, code health analytics, and PR reviews | React 18, TypeScript, Vite, TanStack Query |
| **[`devintel-vscode`](./devintel-vscode)** | VS Code extension with integrated AI chat sidebar and code review commands | TypeScript, VS Code Extension API |

> **What makes this different?** Unlike simple ChatGPT wrappers, DevIntel AI implements a complete **RAG pipeline with AST-aware semantic chunking**, a **self-correcting autonomous agent** with tool-use for PR generation, and **production-grade resilience patterns** (circuit breaker, retry queues, prompt injection defense) — the same patterns used in enterprise AI systems.

---

## ✨ Key Features

### 🤖 AI-Powered Code Intelligence
- **RAG-Powered Chat** — Ask natural language questions about your codebase with streaming SSE responses, backed by pgvector similarity search with context expansion
- **Autonomous Agent** — Instruct the AI to implement features; it drafts a PR plan using OpenAI tool-use (function calling), creates a branch, commits code, and opens a PR on GitHub
- **AI Code Review** — Automatically generates structured reviews on pull requests with severity-tagged issues, security concerns, and performance notes
- **Code Health Analysis** — Multi-dimensional quality scoring (complexity, documentation, maintainability, test coverage, security) using RAG sampling + GPT-4o
- **Auto-Fix Service** — Self-correcting fix generation loop: generates patches via Search/Replace blocks, validates with syntax checking, retries on failure (up to 3 attempts)
- **Test Generation** — AI-generated test suites for code changes with sandbox execution and verification

### 🔐 Enterprise-Grade Security
- **Authentication** — JWT access tokens + SHA-256 hashed refresh tokens via HttpOnly cookies, bcrypt password hashing, GitHub OAuth 2.0
- **Token Encryption** — Fernet AES-256 encryption for stored GitHub tokens at rest
- **Security Headers** — OWASP-compliant middleware (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy)
- **Input Validation** — SQL injection detection middleware, prompt injection defense with regex pattern matching, CSRF protection, request size limiting
- **Audit Logging** — Structured logging of all sensitive operations with request tracing via `X-Request-ID`

### 🔧 Production Infrastructure
- **Resilience** — Circuit breaker pattern (CLOSED → OPEN → HALF_OPEN) on OpenAI API calls with configurable failure thresholds and recovery timeouts
- **Retry Logic** — Exponential backoff retries via `tenacity` for transient API failures (timeouts, rate limits, connection errors)
- **Retry Queue** — Failed indexing tasks are queued for automatic retry with backoff
- **Caching** — Redis-backed cache layer for embedding results and vector search queries with configurable TTL
- **Observability** — Prometheus metrics endpoint, OpenTelemetry-ready structured logging via `structlog`, distributed request tracing
- **Background Processing** — Celery workers with Redis broker for async repository indexing at configurable concurrency

---

## 🏗 System Architecture

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
│                    SSL Termination · Static Assets                         │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FastAPI APPLICATION SERVER                              │
│                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Auth        │  │ Security     │  │ Metrics      │  │ CSRF           │  │
│  │ Middleware  │  │ Headers      │  │ Middleware   │  │ Protection     │  │
│  │ (JWT)       │  │ (OWASP)      │  │ (Prometheus) │  │                │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│         └────────────────┴─────────────────┴───────────────────┘           │
│                                    │                                       │
│  ┌─────────────────────────────────┴─────────────────────────────────────┐ │
│  │                        API v1 ROUTES                                  │ │
│  │  /auth  /repos  /chat  /health-score  /pr-review  /webhooks  /ws     │ │
│  └──────────────────────────────┬────────────────────────────────────────┘ │
│                                 │                                          │
│  ┌──────────────────────────────┴────────────────────────────────────────┐ │
│  │                       SERVICE LAYER                                   │ │
│  │                                                                       │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐                │ │
│  │  │ ChatService │  │ AgentService │  │ PRReviewSvc   │                │ │
│  │  │ (RAG Chat)  │  │ (Tool-Use)   │  │ (AI Reviews)  │                │ │
│  │  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘                │ │
│  │         │                │                   │                        │ │
│  │  ┌──────┴──────┐  ┌──────┴───────┐  ┌───────┴───────┐               │ │
│  │  │ CodeHealth  │  │ AutoFixSvc   │  │ Incremental   │               │ │
│  │  │ Scoring     │  │ (Self-Heal)  │  │ Indexer       │               │ │
│  │  └─────────────┘  └──────────────┘  └───────────────┘               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
┌──────────────────┐  ┌────────────────┐  ┌───────────────────┐
│  PostgreSQL 16   │  │  Redis 7       │  │  OpenAI API       │
│  + pgvector      │  │  Cache/Broker  │  │  (Circuit Breaker │
│  (Embeddings)    │  │  (Celery)      │  │   + Retry)        │
└──────────────────┘  └────────────────┘  └───────────────────┘
```

---

## 🧬 AI / ML Pipeline

### Retrieval-Augmented Generation (RAG)

The core intelligence of DevIntel is a custom RAG pipeline that operates on the semantic structure of code, not raw text:

```
Repository Push Event
        │
        ▼
┌───────────────────────────┐
│  1. File Discovery        │  Filter by supported extensions (.py, .ts, .go, .rs, .java, ...)
│     & Preprocessing       │  Skip ignored dirs (node_modules, .git, __pycache__)
└───────────┬───────────────┘  Enforce max file size (5 MB)
            │
            ▼
┌───────────────────────────┐
│  2. AST-Aware Chunking    │  Tree-sitter parses source into AST
│     (tree_sitter_chunking)│  Split at semantic boundaries (function/class/method definitions)
└───────────┬───────────────┘  Merge small segments to target ~700 tokens per chunk
            │                  Lossless: 100% of source code preserved
            ▼
┌───────────────────────────┐
│  3. Embedding Generation  │  OpenAI text-embedding-3-small (1536-dim)
│     (Batch API)           │  Circuit breaker protection
└───────────┬───────────────┘  Retry with exponential backoff
            │
            ▼
┌───────────────────────────┐
│  4. Vector Storage        │  pgvector cosine similarity index
│     (PostgreSQL)          │  Per-repository partitioned storage
└───────────┬───────────────┘  Incremental upsert with chunk deduplication
            │
            ▼
┌───────────────────────────┐
│  5. Retrieval + Expansion │  Top-K vector similarity search
│                           │  Context window expansion (±1 neighbor chunks)
└───────────┬───────────────┘  Redis caching of repeated queries (TTL: 1h)
            │
            ▼
┌───────────────────────────┐
│  6. Generation            │  GPT-4o with grounded system prompt
│     (Streaming SSE)       │  Multi-turn chat history with token-aware trimming
└───────────────────────────┘  Prompt injection defense (12 regex patterns)
```

### Autonomous Agent Architecture

The Agent Service uses **OpenAI function calling** (tool-use) to plan and execute code changes:

1. **Context Retrieval** — Pulls top-8 most relevant code chunks for the user's instruction
2. **Tool-Use Planning** — Prompts GPT-4o with a `create_pull_request` tool schema; the model generates branch name, PR title/body, commit message, and complete file contents
3. **Validation & Execution** — Parses the tool call response, creates a branch, commits files, and opens a PR via the GitHub API
4. **Optional Test Generation** — Generates and runs tests in a sandbox before committing; blocks the PR if tests fail

### Auto-Fix Self-Correction Loop

The Auto-Fix Service implements a **retry-with-feedback loop** for reliable code generation:

```
Issue Description → Embedding Search → File Context Retrieval
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
                              │     │ Apply Diff +    │
                              │     │ Syntax Check    │──── Pass ──► Commit + Open PR
                              │     └────────┬────────┘
                              │              │
                              │            Fail
                              │              │
                              │              ▼
                              │     ┌─────────────────┐
                              └─────│ Feed Errors to  │
                                    │ LLM for Retry   │
                                    │ (max 3 attempts)│
                                    └─────────────────┘
```

---

## 🛠 Tech Stack

### Backend
| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI 0.109, Uvicorn (ASGI), Pydantic v2 Settings |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic migrations, pgvector 0.2.4 |
| **AI/ML** | OpenAI GPT-4o + text-embedding-3-small, tiktoken tokenizer, Tree-sitter AST parser |
| **Auth** | JWT (python-jose), bcrypt (passlib), Fernet encryption (cryptography), GitHub OAuth 2.0 |
| **Caching** | Redis 7 with async client, configurable TTL and LRU eviction |
| **Task Queue** | Celery 5 with Redis broker (4 concurrent workers) |
| **Resilience** | Circuit breaker (custom), tenacity (retry + backoff), retry queue |
| **Observability** | Prometheus client, structlog (JSON), request ID tracing |
| **Security** | CSRF middleware, SQL injection detection, security headers (HSTS/CSP), request size limiting, audit logging |
| **Testing** | pytest + pytest-asyncio, pytest-cov |

### Frontend
| Category | Technologies |
|----------|-------------|
| **Framework** | React 18, TypeScript 5, Vite 5 |
| **State** | Zustand (global), TanStack Query v5 (server state) |
| **UI** | Radix UI primitives, shadcn/ui, Tailwind CSS, Framer Motion |
| **Forms** | React Hook Form + Zod validation |
| **Routing** | React Router v6 |
| **Charts** | Recharts (code health dashboards) |
| **Testing** | Vitest + Testing Library |

### VS Code Extension
| Category | Technologies |
|----------|-------------|
| **Runtime** | VS Code Extension API (^1.85.0) |
| **Build** | Webpack, TypeScript |
| **Features** | Sidebar webview chat, context menu code review, secure API token storage |

### Infrastructure
| Category | Technologies |
|----------|-------------|
| **Containerization** | Docker multi-stage builds, Docker Compose (prod + dev) |
| **Reverse Proxy** | Nginx 1.25 with SSL termination |
| **CI/CD** | GitHub Actions (lint, test, build, deploy) |
| **Hosting** | Render (API) + Neon (PostgreSQL) + Vercel (Frontend) |
| **Monitoring** | Prometheus + custom metrics endpoint |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ / Bun
- PostgreSQL 16 with [pgvector](https://github.com/pgvector/pgvector) extension
- Redis 7+ (optional for caching/queue)
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
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — fill in all required values (see Environment section below)

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
npm run dev
```

### 4. VS Code Extension (Development)

```bash
cd devintel-vscode

npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host
```

### 5. Docker Compose (Full Stack)

```bash
# Copy and configure production env
cp .env.production.example .env.production
# Fill in all secrets

# Launch all services
docker compose -f docker-compose.prod.yml up -d
```

This starts: PostgreSQL + pgvector, Redis, Backend API, Celery Worker, Nginx reverse proxy, and Prometheus.

---

## ⚙️ Environment Variables

### Backend (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (`postgresql+asyncpg://user:pass@host/db`) |
| `JWT_SECRET_KEY` | ✅ | Secret key for JWT token signing |
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

Generate a Fernet key:
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

### Option A: Free-Tier Stack (Recommended for Demo)

| Service | Provider | Config |
|---------|----------|--------|
| API Server | [Render](https://render.com) | `render.yaml` — Docker web service |
| Database | [Neon](https://neon.tech) | Free PostgreSQL with pgvector |
| Frontend | [Vercel](https://vercel.com) | `vercel.json` — auto-deploys from `devintel-frontend/dist` |

### Option B: Docker Compose (Self-Hosted)

```bash
docker compose -f docker-compose.prod.yml up -d
```

**Includes:** PostgreSQL 16 + pgvector, Redis 7, Backend API (2 CPU / 2GB RAM limit), Celery Worker (4 CPU / 4GB RAM limit), Nginx with SSL, Prometheus monitoring.

### CI/CD

GitHub Actions pipelines in [`.github/workflows/`](./.github/workflows):

- **`ci.yml`** — Lint, type check, unit tests, coverage report on every PR
- **`deploy.yml`** — Automated deployment to Render + Vercel on merge to `main`

---

## 📡 API Reference

Interactive docs available at `http://localhost:8000/docs` (debug mode only).

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/signup` | Register with email/password |
| `POST` | `/api/v1/auth/login` | Login, receive JWT + refresh cookie |
| `GET` | `/api/v1/auth/github` | Initiate GitHub OAuth flow |
| `POST` | `/api/v1/repos/connect` | Connect and index a GitHub repository |
| `POST` | `/api/v1/chat/{repo_id}` | RAG-powered chat (SSE streaming) |
| `POST` | `/api/v1/health-score/{repo_id}/analyze` | Run AI code health analysis |
| `POST` | `/api/v1/pr-review/{repo_id}/{pr_number}` | Generate AI pull request review |
| `POST` | `/api/v1/repos/{repo_id}/agent/draft` | Draft an autonomous PR plan |
| `POST` | `/api/v1/repos/{repo_id}/agent/execute` | Execute drafted PR on GitHub |
| `POST` | `/api/v1/webhooks/github` | Receive GitHub push/PR events |
| `WS` | `/api/v1/ws/{repo_id}` | WebSocket for real-time indexing progress |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |

---

## 📁 Project Structure

```
devintel/
├── devintel-backend/
│   ├── app/
│   │   ├── api/v1/              # Route handlers (auth, chat, repos, webhooks, ws)
│   │   ├── core/                # Config, exceptions, logging, validators
│   │   ├── db/                  # Database session, engine
│   │   ├── integrations/        # OpenAI client (circuit breaker), GitHub client
│   │   ├── middleware/          # Security headers, CSRF, metrics, SQL injection
│   │   ├── models/              # SQLAlchemy models (17 tables)
│   │   ├── repositories/        # Data access layer (repository pattern)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic (24 service modules)
│   │   ├── tasks/               # Celery async tasks
│   │   └── utils/               # Tree-sitter chunking, call graph, patcher, linter
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # pytest test suite
│   ├── Dockerfile               # Multi-stage production build
│   └── Makefile                 # Dev shortcuts
├── devintel-frontend/
│   ├── src/
│   │   ├── components/          # React components (UI + feature)
│   │   ├── hooks/               # Custom React hooks
│   │   ├── pages/               # Route pages (Dashboard, Login, Signup, OAuth)
│   │   ├── store/               # Zustand state management
│   │   ├── lib/                 # Utilities and API client
│   │   └── types/               # TypeScript type definitions
│   └── tests/                   # Vitest test suite
├── devintel-vscode/
│   └── src/
│       ├── extension.ts         # Extension activation & commands
│       ├── sidebar.ts           # Webview chat panel
│       └── auth.ts              # Token management
├── .github/workflows/           # CI/CD (ci.yml, deploy.yml)
├── docker-compose.prod.yml      # Full production stack
├── nginx/                       # Nginx config + SSL
├── prometheus/                  # Prometheus scrape config
└── render.yaml                  # Render.com IaC
```

---

## 🧪 Testing

```bash
# Backend tests
cd devintel-backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend tests
cd devintel-frontend
npm run test

# Lint
npm run lint
```

---

## 🔑 Engineering Decisions

| Decision | Rationale |
|----------|-----------|
| **Tree-sitter AST chunking over naive text splitting** | Preserves semantic boundaries (functions, classes) → higher retrieval precision for RAG |
| **pgvector over Pinecone/Weaviate** | Zero vendor lock-in, collocated with relational data, native PostgreSQL joins for filtering |
| **Circuit breaker on OpenAI client** | Prevents cascading failures during API outages; auto-recovers via HALF_OPEN state |
| **Search/Replace patches over full file rewrites** | Minimizes LLM output tokens and reduces hallucination surface in auto-fix |
| **Prompt injection defense in ChatService** | 12 regex patterns catch common injection vectors before they reach the system prompt |
| **Fernet AES-256 for GitHub tokens** | Symmetric encryption with authenticated encryption (HMAC) — secure at rest, fast to decrypt |
| **SHA-256 hashed refresh tokens** | Tokens are never stored in plaintext; lookup by hash, compare server-side |
| **Context expansion (±1 chunks)** | Adjacent chunks inherit 95% relevance → provides semantic continuity in RAG responses |
| **Celery for indexing** | Repository indexing is CPU-heavy (tree-sitter parsing + embedding generation); async workers prevent API blocking |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file.

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](./CONTRIBUTING.md) before opening a PR.

See the [Changelog](./CHANGELOG.md) for release history.

---

<p align="center">
  Built with ☕ and a lot of async/await<br/>
  <strong>Joseph Kamau</strong> — <a href="https://github.com/josephkamau32">@josephkamau32</a>
</p>
