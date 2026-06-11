# DevIntel AI — Production-Grade Autonomous Code Patching & RAG Platform

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/josephkamau32/devintel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react&logoColor=white)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1.svg?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991.svg?logo=openai&logoColor=white)](https://openai.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**DevIntel AI** is a production-grade, full-stack AI platform that integrates autonomous agentic workflows into development pipelines. By connecting GitHub repositories, developers can run deep semantic search queries, interact with codebase-aware chatbots via **Retrieval-Augmented Generation (RAG)**, auto-generate PR reviews, and launch **autonomous code patching agents** that write and self-correct syntax bugs before issuing pull requests.

---

## 🏗️ Architecture & How It Works

```
[1. GitHub OAuth] ──> [2. AST Parser (Tree-Sitter)] ──> [3. pgvector Storage]
                                                               │
                                                               ▼
[5. GitHub Pull Request] <── [4. Autonomous Agent (OpenAI)] <──┘
 (Headless Branch + PR)       (Patching + Self-Correction Loop)
```

1. **Connect & Auth**: Secure login via GitHub OAuth. Access tokens are dynamically encrypted at rest using **Fernet AES-256** encryption.
2. **AST-Aware Parsing**: Repository codebases are ingested and parsed using **Tree-Sitter** to generate high-signal AST code blocks rather than naive character/token chunks.
3. **Semantic Storage**: Code fragments are embedded using `text-embedding-3-small` (1536 dimensions) and indexed in a **PostgreSQL** database utilizing **pgvector** with Cosine Similarity indexers.
4. **Agentic Loop**: Given a code issue, the AI agent performs semantic retrieval, designs a **Unified Diff Patch**, validates the syntax using a localized linting pass, corrects its own syntax errors if any arise, and tests the output.
5. **Git Deployment**: The agent dynamically logs into GitHub on behalf of the user, creates a temporary headless branch, commits the validated patch, and opens a new **Pull Request** for reviewer inspection.

---

## 🤖 Deep Dive: AI/ML Engineering & Core Systems

### 1. AST-Aware Tree-Sitter Ingestion
Traditional RAG pipelines use fixed-size character chunking, which splits code down the middle of functions, destroying syntactic context. DevIntel AI uses language-specific grammar packages via **Tree-Sitter** to:
* Extract logical nodes (e.g., classes, methods, function declarations, loops).
* Reassemble children nodes into functional context blocks.
* Append parent context metadata (e.g., class names, global declarations) to each chunk, guaranteeing that the LLM has complete signature information when writing patches.

### 2. High-Performance pgvector Querying
Our search service runs dynamic distance querying using PostgreSQL `pgvector`:
$$\text{Cosine Distance} = 1 - \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$
This ensures search results match semantic intent rather than simple string hashes, bringing semantic lookups down to **sub-10ms** response latencies.

### 3. Unified Diff Patching & Context Efficiency
Instead of requesting the LLM to output full file code (which is slow, expensive, and risks token truncation), DevIntel AI forces the AI model to output standard **Unified Diff Hunks** (Search/Replace blocks). The backend patch engine dynamically applies these hunks line-by-line while preserving target file offsets.

### 4. AST Validator & Self-Correction Loop
LLMs are prone to hallucinating missing imports, incorrect variable names, or unclosed parenthesis. The agent runs a self-correction compiler loop:
```
           ┌──────────────────────────────────┐
           │   Generate Unified Diff Patch    │
           └────────────────┬─────────────────┘
                            │
                            ▼
           ┌──────────────────────────────────┐
           │ Run Syntax Linter (jsbeautifier) │
           └────────────────┬─────────────────┘
                            │
             [Syntax Errors Found?]
             ├── Yes ──> [Append compiler logs to prompt] ──┐
             │                                              │
             └── No                                         ▼
                 │                          ┌──────────────────────────────┐
                 ▼                          │ Self-Correction Prompt Loop  │
       ┌───────────────────┐                └──────────────────────────────┘
       │ Commit & Create PR│
       └───────────────────┘
```
This loop executes up to 3 times in-memory, completely filtering out syntax bugs before they can reach GitHub.

---

## 🚢 Free-Tier Deployment Guide

DevIntel AI has been optimized to deploy **100% free** on **Vercel** (frontend), **Render** (backend API), and **Neon** (database). 

### 💡 Why It Fits Rendering & Hosting Free Limits
* **Inference Offloading**: Because all heavyweight AI tasks (embeddings and text generation) are offloaded to **OpenAI's API endpoints**, the server consumes almost no CPU or memory.
* **Lightweight ASGI Server**: The API runs on a FastAPI + Uvicorn engine, keeping the base memory consumption under **100MB RAM** (well below Render's 512MB limit).
* **Pre-Built Dependency Wheels**: The backend uses compiled pre-built wheels for dependencies (such as `tree-sitter`, `tiktoken`), eliminating Render build timeout issues from compiling C packages from source.
* **Memory-Optimized Local Caching**: If a Celery/Redis instance is omitted, the API safely falls back to a thread-safe, in-process cache and background task worker.

---

### Step 1: Set Up Neon Database (PostgreSQL + pgvector)
1. Go to [Neon.tech](https://neon.tech/) and sign up for a free account.
2. Create a new project named `devintel`.
3. In the Neon Dashboard, navigate to **SQL Editor** and run the following command to enable the vector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Copy the connection string (it will look like `postgresql://alex:passwd@ep-cool-snowflake-1234.us-east-2.neon.tech/neondb?sslmode=require`).
5. Replace `postgresql://` with `postgresql+asyncpg://` at the beginning of the string to support FastAPI's asynchronous drivers (e.g., `postgresql+asyncpg://alex:passwd@...`).

### Step 2: Set Up Render Backend (Web Service)
1. Sign up on [Render.com](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Link your GitHub repository and choose the `devintel` repository.
4. Set the following build options:
   * **Name**: `devintel-api`
   * **Region**: Choose the region closest to you
   * **Root Directory**: `devintel-backend`
   * **Language**: `Docker` (Render will automatically detect the production `Dockerfile`)
   * **Instance Type**: `Free`
5. Click **Advanced** and add the following Environment Variables:

| Environment Variable | Value / Description |
| :--- | :--- |
| **ENVIRONMENT** | `production` |
| **DEBUG** | `false` |
| **DATABASE_URL** | *Your modified Neon connection string (from Step 1)* |
| **OPENAI_API_KEY** | *Your OpenAI API Key* |
| **OPENAI_CHAT_MODEL** | `gpt-4o` |
| **TOKEN_ENCRYPTION_KEY** | *A 32-byte Base64 key (Generate via: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) * |
| **SECRET_KEY** | *A random hex string (Generate via: `python -c "import secrets; print(secrets.token_hex(32))"`) * |
| **JWT_SECRET_KEY** | *A second random hex string* |
| **GITHUB_CLIENT_ID** | *Your GitHub OAuth App Client ID (See Step 4)* |
| **GITHUB_CLIENT_SECRET** | *Your GitHub OAuth App Client Secret (See Step 4)* |
| **GITHUB_REDIRECT_URI** | `https://devintel-api.onrender.com/api/v1/auth/github/callback` (Change `devintel-api.onrender.com` to your Render app domain) |
| **CORS_ORIGINS** | `["https://devintel-frontend.vercel.app"]` (Change to your Vercel deployment URL from Step 3) |

6. Deploy the web service. Render will build the Docker container and start serving on HTTPS automatically.

### Step 3: Set Up Vercel Frontend
1. Sign up on [Vercel.com](https://vercel.com/).
2. Click **Add New** -> **Project** and select your `devintel` repository.
3. Vercel will auto-detect the workspace structure because we have configured [vercel.json](file:///c:/Users/HP/Documents/Projects/devintel/vercel.json) at the root level.
4. Keep the root directory configuration as the root of the repository. Vercel will execute the custom build commands specified in our configuration:
   * **Build Command**: `npm run build --prefix devintel-frontend`
   * **Install Command**: `npm install --prefix devintel-frontend`
   * **Output Directory**: `devintel-frontend/dist`
5. Under **Environment Variables**, add:
   * **VITE_API_URL**: `https://devintel-api.onrender.com` (Your Render API URL)
6. Click **Deploy**. Vercel will build and serve your static Vite bundle on a global CDN. Copy your Vercel project URL (e.g. `https://devintel-frontend.vercel.app`).

### Step 4: Configure GitHub OAuth App
1. Go to your GitHub profile settings -> **Developer Settings** -> **OAuth Apps** -> **New OAuth App**.
2. Set configuration values:
   * **Application Name**: `DevIntel AI`
   * **Homepage URL**: `https://devintel-frontend.vercel.app` (Your Vercel URL)
   * **Authorization callback URL**: `https://devintel-api.onrender.com/api/v1/auth/github/callback` (Your Render API Callback URL)
3. Generate a **Client Secret** and copy both the **Client ID** and **Client Secret** into your Render environment variables (from Step 2). Re-deploy Render backend if needed to load the keys.

---

## 🔧 Local Development & Quick Start

### Prerequisites
* Python 3.11+ & Virtual Environment
* Node.js 18+ & npm
* Docker & Docker Compose (optional for local PostgreSQL)

### Run with Local Scripts (Automated)
Run the following script at the root directory to automatically verify dependencies, set up environments, and run both services:

```powershell
# Windows
.\scripts\start.ps1
```

```bash
# Linux/MacOS
./scripts/start.sh
```

---

## 🔬 Local Manual Ingress Testing

To test individual components locally:

```bash
# 1. Run Backend Tests
cd devintel-backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest tests/

# 2. Run Frontend Build Checks
cd devintel-frontend
npm install
npm run build
```

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
