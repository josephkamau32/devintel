# DevIntel AI

DevIntel AI is a production-grade AI coding assistant platform with secure authentication, GitHub OAuth, repository connection placeholders, and a React 18 TypeScript frontend.

## Stack

- Backend: FastAPI, SQLAlchemy async, Alembic, PostgreSQL + pgvector, OpenAI
- Frontend: React 18, TypeScript, Vite, TanStack Query v5, Zustand, Tailwind CSS

## Auth-first implementation

Phase 1 is complete: email/password signup, login, logout, refresh-token cookie handling, JWT access tokens, GitHub OAuth redirect/callback, bcrypt password hashing, Fernet-encrypted GitHub tokens, CORS with credentials, and Pydantic Settings validation.

## Backend quick start

```bash
cd devintel-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install aiosqlite
cp .env.example .env
# Fill DATABASE_URL, JWT_SECRET_KEY, SECRET_KEY, TOKEN_ENCRYPTION_KEY, GitHub OAuth, OpenAI, and CORS_ORIGINS.
alembic upgrade head
pytest tests/ -v
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` in debug mode to inspect auth endpoints.

## Frontend quick start

```bash
cd devintel-frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173` to use the login and signup flows.

## Environment

Backend `.env` requires:

- `DATABASE_URL` using `postgresql+asyncpg://`
- `JWT_SECRET_KEY`
- `SECRET_KEY`
- `TOKEN_ENCRYPTION_KEY` generated with Fernet
- GitHub OAuth client ID, secret, and redirect URI
- `OPENAI_API_KEY`
- `CORS_ORIGINS` as a JSON array, for example `["http://localhost:5173"]`

Frontend `.env` requires:

```env
VITE_API_URL=http://localhost:8000
```
