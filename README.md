# DevIntel AI — Production-Grade Autonomous Code Patching & RAG Platform

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/josephkamau32/devintel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6.svg?logo=typescript)](https://www.typescriptlang.org/)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1.svg?logo=postgresql)](https://github.com/pgvector/pgvector)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991.svg?logo=openai)](https://openai.com/)

> **DevIntel AI** transforms how developers interact with codebases through AI-powered semantic search, RAG chatbots, and autonomous code modification agents. Securely connect your GitHub repositories and let our platform help you understand, refactor, and improve your code.

## Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Testing](#-testing)
- [Architecture Decisions](#-architecture-decisions)

## Features

### Core Capabilities
- **AST-Aware Semantic Chunking** — Tree-Sitter powered parsing preserves syntactic boundaries for accurate RAG context
- **Vector Similarity Search** — pgvector with HNSW indexes for sub-10ms semantic lookups
- **RAG Chat Interface** — Codebase-aware conversational AI with streaming responses
- **Autonomous PR Generation** — AI agents that draft, validate, and create pull requests
- **Self-Correction Loop** — Automatic syntax validation and retry for generated code
- **PR Review Automation** — AI-powered code review comments on pull requests

### Security & Resilience
- **Multi-Modal Authentication** — GitHub OAuth + Email/Password with JWT tokens
- **AES-256 Token Encryption** — GitHub tokens encrypted at rest using Fernet
- **Circuit Breaker Pattern** — Graceful degradation during OpenAI API outages
- **Rate Limiting** — Per-endpoint throttling to prevent abuse
- **CSRF Protection** — Double-submit cookie pattern for state-changing operations
- **SQL Injection Detection** — Input validation middleware for all endpoints

### Production Ready
- **Free-Tier Optimized** — Runs on Render (512MB RAM) + Neon (free Postgres) + Vercel
- **Dual-Mode Cache** — Redis support with in-memory fallback
- **Async-First Architecture** — Non-blocking I/O throughout the stack
- **Structured Logging** — JSON logs with request tracing and audit trails

## Architecture

```
[GitHub OAuth] ──> [Tree-Sitter Parser] ──> [pgvector Storage]
                                                              │
                                                              ▼
[GitHub PR] <── [OpenAI Agent (RAG + Tools)] <── [Unified Diff Patcher]
     │                                                │
     └─ Creates headless branch, commits, opens PR       └─ Validates syntax, retries on failure
```

### Data Flow

1. **Connect** — User authenticates via GitHub OAuth; tokens encrypted with Fernet AES-256
2. **Index** — Repository cloned, parsed via Tree-Sitter, chunked at semantic boundaries, embedded via OpenAI
3. **Query** — User questions processed through vector similarity search with cosine distance
4. **Generate** — Agent retrieves relevant chunks, calls LLM with tool functions
5. **Validate** — Syntax linter checks generated code; up to 3 retry attempts
6. **Deploy** — Validated patch committed to headless branch, PR opened on GitHub

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | FastAPI 0.109+ | Async HTTP framework |
| ORM | SQLAlchemy 2.0 | Database modeling |
| Vector DB | PostgreSQL + pgvector | Embedding storage with HNSW indexes |
| AI | OpenAI GPT-4o + text-embedding-3-small | LLM inference |
| Frontend | React 18 + TypeScript | UI framework |
| State | TanStack Query | Server state management |
| Styling | Tailwind CSS | Utility-first CSS |
| Auth | python-jose + passlib | JWT + password hashing |
| Parsing | Tree-Sitter | AST-aware code chunking |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### Automated Setup

```powershell
# Windows
.\scripts\start.ps1
```

```bash
# Linux/MacOS
./scripts/start.sh
```

### Manual Setup

```bash
# Backend
cd devintel-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Generate required secrets
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # TOKEN_ENCRYPTION_KEY
python -c "import secrets; print(secrets.token_hex(32))"  # JWT_SECRET_KEY, SECRET_KEY

# Create .env file with required variables (see .env.example)
cp .env.example .env

# Run migrations & start server
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
# Frontend
cd devintel-frontend
npm install
npm run dev
```

## Deployment

### Free-Tier Deployment

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| Neon | PostgreSQL + pgvector | 20M rows, 20GB storage |
| Render | FastAPI backend | 750hrs/month (512MB RAM) |
| Vercel | React frontend | 100GB bandwidth |

### Environment Variables

```env
# Required
DATABASE_URL=postgresql+asyncpg://...
OPENAI_API_KEY=sk-...
TOKEN_ENCRYPTION_KEY=...  # Fernet key
JWT_SECRET_KEY=...        # HS256 secret
SECRET_KEY=...            # CSRF secret

# GitHub OAuth
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=https://your-api.onrender.com/api/v1/auth/github/callback

# CORS (set to your frontend URL)
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

See [SETUP.md](SETUP.md) for detailed deployment instructions.

## API Documentation

### Generate OpenAPI Schema

```bash
cd devintel-backend
python scripts/generate_openapi.py
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/signup` | POST | Email/password registration |
| `/api/v1/auth/login` | POST | Email/password login |
| `/api/v1/auth/github` | GET | GitHub OAuth redirect |
| `/api/v1/auth/github/callback` | GET | OAuth callback handler |
| `/api/v1/auth/refresh` | POST | JWT refresh |
| `/api/v1/chat` | POST | Streaming RAG chat |
| `/api/v1/chat/draft` | POST | Agent PR draft |
| `/api/v1/chat/execute` | POST | Execute drafted PR |
| `/api/v1/repos` | POST | Connect repository |
| `/api/v1/repos/index` | POST | Trigger indexing |
| `/api/v1/repos/{id}/search` | GET | Semantic search |

## Development

### Project Structure

```
devintel/
├── devintel-backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers
│   │   ├── core/            # Config, security, constants
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Database operations
│   │   ├── services/        # Business logic
│   │   └── utils/           # Tree-sitter, patcher, etc.
│   ├── tests/               # Pytest suite
│   └── scripts/             # Utility scripts
├── devintel-frontend/
│   ├── src/
│   │   ├── pages/           # Route components
│   │   ├── components/      # Shared UI components
│   │   ├── hooks/           # React hooks
│   │   └── lib/             # API clients
│   └── tests/               # Vitest + Playwright
├── devintel-vscode/         # VS Code extension
└── docs/
    └── adr/                 # Architecture decisions
```

### Running Tests

```bash
# Backend
cd devintel-backend
pytest tests/ --cov=app

# Frontend unit tests
cd devintel-frontend
npm run test

# Frontend E2E tests
npm run test:e2e
```

## Architecture Decisions

Key architectural choices are documented in [Architecture Decision Records](docs/adr/):

- [ADR-001](docs/adr/001-tree-sitter-chunking.md) — Tree-Sitter AST chunking vs naive splitting
- [ADR-002](docs/adr/002-openai-circuit-breaker.md) — Circuit breaker for API resilience
- [ADR-003](docs/adr/003-dual-authentication.md) — Multi-modal authentication strategy

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.