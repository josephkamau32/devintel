# DevIntel AI

[![CI](https://github.com/josephkamau32/devintel/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/josephkamau32/devintel/actions/workflows/ci.yml)

An asynchronous code intelligence platform that indexes codebases into a PostgreSQL vector database, provides context-grounded retrieval-augmented generation (RAG) for codebase questions, calculates multi-dimensional code health metrics, generates AST-based architecture diagrams, and automates pull request reviews.

The system is deployed as a monorepo containing a FastAPI backend, a React/TypeScript frontend, and a companion VS Code extension.

## Live Demo

A public deployment is accessible at [devintel.vercel.app](https://devintel.vercel.app).

* **Frontend:** Hosted on Vercel.
* **Backend API:** Hosted on Render as a containerized service.
* **Database:** Managed PostgreSQL 16 with the `pgvector` extension on Render.
* **Demo Access:** The application includes a demo mode (`DEMO_MODE=true`) that enables evaluation via a pre-seeded repository (`devintel/devintel-core`) without requiring GitHub OAuth setup.

---

## Subsystems

| Directory | Responsibility | Technologies |
|---|---|---|
| [`devintel-backend`](./devintel-backend) | Asynchronous API, RAG pipeline, background job poller, and GitHub integrations | Python 3.11, FastAPI 0.109, SQLAlchemy 2.0 (asyncpg), pgvector, Google GenAI SDK, OpenAI SDK |
| [`devintel-frontend`](./devintel-frontend) | Single-page application for repository management, streaming chat, and analytics | React 18, TypeScript 5, Vite 5, Tailwind CSS, TanStack Query v5, Zustand, Mermaid.js |
| [`devintel-vscode`](./devintel-vscode) | Developer extension providing a sidebar chat interface and context-menu reviews | TypeScript, VS Code Extension API, Webpack |

---

## System Architecture

```mermaid
graph TD
    subgraph Clients
        FE["React SPA (Vite)"]
        VSC["VS Code Extension"]
        GH["GitHub Webhooks"]
    end

    FE --> API["FastAPI Application Server"]
    VSC --> API
    GH --> API

    subgraph Backend["FastAPI Backend (devintel-backend)"]
        MW["Middleware Stack<br/>Security Headers · CORS · Rate Limiting · Request ID · Audit Logging"]
        ROUTES["API v1 Endpoints<br/>/auth · /repos · /chat · /architecture · /pr-review · /webhooks"]
        SVC["Service Layer<br/>ChatService · CodeHealthService · ArchitectureService · PRReviewService"]
        POLLER["Asyncio Job Poller<br/>(SELECT ... FOR UPDATE SKIP LOCKED)"]
        REPO["Repository Layer (SQLAlchemy 2.0 Async)"]

        MW --> ROUTES
        ROUTES --> SVC
        ROUTES --> REPO
        SVC --> REPO
        POLLER --> SVC
        POLLER --> REPO
    end

    subgraph Storage["Data Tier"]
        PG[("PostgreSQL 16 + pgvector<br/>Repositories · Chunks · Embeddings · Diagrams · Jobs")]
        REDIS[("Redis 7 (Optional)<br/>Distributed Rate Limiting · Search Cache")]
    end

    subgraph AIProviders["External AI Services"]
        GEMINI["Google Gemini API<br/>gemini-3.6-flash · gemini-embedding-001 (Default)"]
        OPENAI["OpenAI API<br/>gpt-4o · text-embedding-3-small (Optional)"]
    end

    REPO --> PG
    SVC --> REDIS
    MW --> REDIS
    SVC --> GEMINI
    SVC --> OPENAI
```

### Architectural Structure

The backend follows a layered architecture with explicit dependency separation:

1. **Routing Layer (`app/api/v1/`):** Request validation via Pydantic schemas, dependency injection for sessions and current user authentication.
2. **Service Layer (`app/services/`):** Business logic, RAG orchestration, LLM provider integration, AST processing, and patch validation.
3. **Repository Layer (`app/repositories/`):** Encapsulated data access using async SQLAlchemy 2.0 queries.
4. **Data Models (`app/models/`):** Relational tables including repository metadata, code chunks, vector embeddings, architecture diagrams, code health scores, and indexing jobs.

---

## Core Technical Features

### 1. AST-Aware Code Chunking and Indexing

Code files are processed using Tree-sitter parsers (`tree-sitter` and `tree-sitter-language-pack`) to split code along syntactic unit boundaries (classes, functions, and methods) rather than arbitrary character or line offsets:

* **Target Chunk Size:** 1,000 characters with a 200-character overlap window (`app/core/config.py`).
* **Language Support:** Python, TypeScript, JavaScript, Go, Rust, Java, C, C++, Ruby, PHP, and Markdown.
* **Fallback Strategy:** If an AST grammar is unavailable or parsing fails, a line-based token-preserving fallback partitioner is used.
* **File Filtering:** Files matching `IGNORED_DIRECTORIES` (e.g. `node_modules`, `.git`, `venv`, `__pycache__`, `dist`) or exceeding `MAX_FILE_SIZE_MB` (5 MB default) are excluded from ingestion.

### 2. Embeddings and Vector Retrieval

The retrieval engine generates vector representations and performs similarity matching directly in PostgreSQL:

* **Default AI Provider:** Google Gemini API using `gemini-embedding-001` with Matryoshka dimension reduction to 768 dimensions (`app/core/config.py`).
* **Alternative Provider:** OpenAI API using `text-embedding-3-small` (1,536 dimensions) when `AI_PROVIDER=openai` is selected.
* **Vector Index:** PostgreSQL `vector` columns indexed using the `pgvector` extension with cosine distance operator (`<=>`).
* **Context Expansion:** When a relevant chunk is retrieved, adjacent chunks (window of plus/minus 1 chunk index from the same file) are pulled to maintain function signature and caller context continuity.
* **Hybrid Retrieval (Optional):** Supports combining vector similarity search with in-memory BM25 lexical search using Reciprocal Rank Fusion (RRF in `app/services/retrieval/rrf.py`).

### 3. Asynchronous Task Processing

Repository ingestion and heavy analysis tasks are handled asynchronously without blocking HTTP request threads:

* **Job Poller:** An in-process background asyncio worker (`app/services/job_poller.py`) running within the FastAPI lifecycle.
* **Queue Mechanism:** Jobs are queued in the PostgreSQL `indexing_jobs` table and claimed using `SELECT ... FOR UPDATE SKIP LOCKED`.
* **Concurrency:** Up to 3 concurrent worker tasks poll the job table every 2.0 seconds.
* **Job Types:** Handles full repository indexing, incremental commit updates, and post-indexing code health analysis.

### 4. Code Health Scoring

`CodeHealthService` (`app/services/code_health_service.py`) calculates multi-dimensional repository quality assessments:

* **Sampling:** Extracts 10 representative chunks across distinct functional areas of the repository.
* **Dimensions:** Computes an overall score (0 to 100) and sub-scores for Complexity, Documentation, Maintainability, Test Coverage, and Security.
* **Output:** Generates a high-level summary, top identified issues, and actionable technical recommendations.

### 5. Architecture Diagram Generation

`ArchitectureVisualizationService` (`app/services/architecture_service.py`) dynamically maps the repository structure:

* **Analysis:** Parses stored code embeddings and files to construct a dependency graph of top-level modules, declared classes, functions, and inter-module import references.
* **Format:** Emits valid Mermaid.js flowchart syntax (`graph TD` with module subgraphs and directional call/import count edges).
* **Display:** Rendered client-side using Mermaid 11 on the repository overview page.

### 6. Automated Pull Request Review and Auto-Fix

* **PR Review (`app/services/pr_review_service.py`):** Parses unified Git diffs, retrieves relevant context from indexed embeddings, and prompts the LLM to output structured JSON reviews with severity-categorized issues (critical, warning, suggestion) and line-specific annotations.
* **Auto-Fix Loop (`app/services/auto_fix_service.py`):** Generates targeted search/replace patch plans for detected health issues, validates that the search target exists in the target file, validates syntax via Python `ast.parse`, retries with error feedback up to 3 times, and optionally creates a Git branch and Pull Request via the GitHub REST API.

### 7. Security Architecture

* **Authentication:** Access tokens via short-lived JWTs (30-minute expiration) and refresh tokens (7-day expiration) stored as SHA-256 hashes in the database and delivered via HttpOnly cookies.
* **Password Hashing:** Implemented using direct `bcrypt` hashing with salt rounds.
* **Credential Encryption:** GitHub OAuth access tokens are encrypted at rest using Fernet symmetric AES-256 encryption (`cryptography` library).
* **HTTP Hardening:** Security middleware applies Content Security Policy (CSP), HTTP Strict Transport Security (HSTS in production), X-Content-Type-Options (`nosniff`), X-Frame-Options (`DENY`), Referrer-Policy, and Permissions-Policy.
* **Input Defense:** SQL injection detection middleware scans query parameters and body payloads for common exploitation patterns. Prompt injection patterns are filtered using regex scanners in `ChatService`.
* **Rate Limiting:** Sliding-window rate limiter per user IP/ID (`RATE_LIMIT_PER_MINUTE=100`) backed by Redis, with a memory-backed fallback when Redis is unconfigured.
* **Metrics Protection:** The Prometheus metrics endpoint (`/metrics`) requires an `X-Metrics-Key` header or Bearer token matching `METRICS_API_KEY`, returning 404 if unauthorized.

---

## Tech Stack

### Backend
* **Language:** Python 3.11
* **Web Framework:** FastAPI 0.109.2, Uvicorn 0.27.1
* **Database Layer:** PostgreSQL 16, SQLAlchemy 2.0.27 (asyncpg 0.29.0), Alembic 1.13.1, pgvector 0.2.4
* **AI Providers:** Google GenAI SDK 2.22.0 (`gemini-3.6-flash`, `gemini-embedding-001`), OpenAI Python SDK 1.12.0 (`gpt-4o`, `text-embedding-3-small`)
* **Code Analysis:** Tree-sitter 0.25.2, tree-sitter-language-pack 0.13.0
* **Resilience:** Tenacity 8.2.3, custom three-state circuit breaker
* **Observability:** Prometheus client 0.20.0, Structlog 24.1.0

### Frontend
* **Runtime / Framework:** Node.js 18+, React 18.3.1, TypeScript 5.3.3
* **Build Tool:** Vite 5.1.1
* **Styling:** Tailwind CSS 3.4.1
* **State & Data Fetching:** Zustand 4.5.0, TanStack React Query 5.18.1
* **Visualization:** Mermaid.js 11.16.1
* **Icons:** Lucide React 0.323.0

### Infrastructure
* **Backend Hosting:** Render Web Service (Docker container deployment)
* **Database Hosting:** Render Managed PostgreSQL 16 with `pgvector`
* **Frontend Hosting:** Vercel (static single-page application)
* **Containerization:** Multi-stage Docker build (`devintel-backend/Dockerfile`)

---

## Local Development Setup

### Prerequisites
* Python 3.11
* Node.js 18 or higher
* PostgreSQL 16 with the `pgvector` extension installed
* An API key for Google Gemini (default) or OpenAI
* (Optional) Redis 7 for distributed caching and rate limiting

### 1. Repository Setup

```bash
git clone https://github.com/josephkamau32/devintel.git
cd devintel
```

### 2. Backend Setup

```bash
cd devintel-backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and supply your DATABASE_URL and GEMINI_API_KEY (or OPENAI_API_KEY)

# Apply database schema migrations
alembic upgrade head

# Start development API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend health:
```bash
curl http://localhost:8000/health
```

### 3. Frontend Setup

```bash
cd ../devintel-frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend application will be available at `http://localhost:5173`.

### 4. Seeding Demo Data (Optional)

To seed the local database with the bounded `devintel-core` repository scope without performing full external GitHub cloning:

```bash
cd devintel-backend
python scripts/seed_demo.py
```

---

## Environment Variables

### Backend Configuration (`devintel-backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | - | PostgreSQL connection URL with asyncpg driver (e.g. `postgresql+asyncpg://postgres:password@localhost:5432/devintel`) |
| `JWT_SECRET_KEY` | Yes | - | Secret key used for signing authentication JWTs (minimum 32 characters) |
| `SECRET_KEY` | Yes | - | Application secret used for cryptographic operations and CSRF tokens |
| `TOKEN_ENCRYPTION_KEY` | Yes | - | 32-byte URL-safe base64-encoded Fernet key for encrypting GitHub tokens at rest |
| `AI_PROVIDER` | No | `gemini` | Primary AI provider: `gemini` or `openai` |
| `GEMINI_API_KEY` | Conditional | - | Required when `AI_PROVIDER=gemini` |
| `GEMINI_CHAT_MODEL` | No | `gemini-3.6-flash` | Gemini model for conversational reasoning |
| `GEMINI_EMBEDDING_MODEL` | No | `gemini-embedding-001` | Gemini model for vector embeddings |
| `OPENAI_API_KEY` | Conditional | - | Required when `AI_PROVIDER=openai` |
| `OPENAI_CHAT_MODEL` | No | `gpt-4o` | OpenAI model for chat completion |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | OpenAI model for vector embeddings |
| `EMBEDDING_DIMENSIONS` | No | `768` | Vector dimension size (768 for Gemini, 1536 for OpenAI) |
| `GITHUB_CLIENT_ID` | Conditional | - | GitHub OAuth application client ID |
| `GITHUB_CLIENT_SECRET` | Conditional | - | GitHub OAuth application client secret |
| `GITHUB_REDIRECT_URI` | Conditional | - | GitHub OAuth callback URL |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | JSON array of permitted origin URLs |
| `REDIS_URL` | No | `None` | Optional Redis connection URL (e.g. `redis://localhost:6379/0`) |
| `DEMO_MODE` | No | `true` | Allows one-click demo login without external OAuth setup |
| `METRICS_API_KEY` | No | `""` | Secret key required to access `/metrics` (fails closed if empty) |

### Generating Required Keys

```bash
# JWT_SECRET_KEY and SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# TOKEN_ENCRYPTION_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend Configuration (`devintel-frontend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_URL` | Yes | `http://localhost:8000` | Base URL of the backend API |

---

## Testing and Verification

### Backend Tests

The backend test suite includes unit tests, repository mocks, validation tests, and integration flows using `pytest` and `pytest-asyncio`:

```bash
cd devintel-backend
pytest tests/ -v
```

To run with coverage reporting:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

* **Test Suite Size:** 55 test modules in `devintel-backend/tests/`.
* **Passing Tests:** 471 unit and mocked integration tests.
* **Statement Coverage:** 61% across the `app/` codebase.

### Frontend Tests

```bash
cd devintel-frontend
npm run test
npm run lint
```

---

## Known Limitations

1. **In-Process Background Task Execution:** Background repository indexing and code health analysis run via an asynchronous job poller (`app/services/job_poller.py`) inside the main FastAPI process. While effective for single-instance deployments, scaling to high ingestion volumes requires migrating this worker to a decoupled task runner.
2. **Auto-Fix AST Validation Scope:** The automated patching loop verifies syntax correctness using Python's native `ast.parse`. Syntax validation for other programming languages is not currently validated prior to pull request generation.
3. **Architecture Diagram Granularity:** Diagrams are synthesized from top-level module directories and Python import statements present in indexed chunks. Runtime call graphs, third-party service dependencies, and dynamic reflections are not inferred.
4. **Code Health Sampling Approach:** Code health metrics are derived from multi-probe representative sampling (10 chunks per repository) passed to an LLM evaluator, rather than exhaustive full-codebase static analysis linters (e.g. SonarQube or Bandit).
5. **Ingestion File Constraints:** Ingestion is restricted to text files under 5 MB with supported source extensions. Binary files, compiled assets, minified bundles, and non-UTF-8 encodings are discarded.

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
