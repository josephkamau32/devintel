# DevIntel - Quick Setup Guide

## 🎯 What This Setup Includes

This monorepo contains the complete DevIntel AI platform:
- **Backend**: FastAPI with RAG pipeline, PostgreSQL, Redis, Celery
- **Frontend**: React + Vite + TypeScript with shadcn-ui
- **Automation Scripts**: One-command startup for both services

---

## 🚀 Quick Start (3 Steps)

### 1️⃣ Configure Backend Environment

```powershell
# Navigate to backend
cd devintel-backend

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# - GITHUB_CLIENT_ID
# - GITHUB_CLIENT_SECRET
# - OPENAI_API_KEY
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
```

### 2️⃣ Start All Services

```powershell
# Windows PowerShell
.\scripts\start.ps1

# Linux/Mac
./scripts/start.sh
```

**The script will automatically:**
- ✅ Check and create `.env` file if missing
- ✅ Start backend with Docker Compose
- ✅ Install frontend dependencies (if needed)
- ✅ Start frontend dev server
- ✅ Display all access URLs

### 3️⃣ Access Your Application

Once both services are running:

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🛑 Stopping Services

```powershell
# Windows PowerShell
.\scripts\stop.ps1

# Linux/Mac
./scripts/stop.sh
```

---

## 📋 Prerequisites

Before running the setup:

✅ **Docker Desktop** - Download from [docker.com](https://www.docker.com/)
✅ **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
✅ **GitHub OAuth App** - Create at [GitHub Settings](https://github.com/settings/developers)
✅ **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/)

---

## 🔧 Manual Setup (Alternative)

If you prefer to run services separately:

### Backend Only

```bash
cd devintel-backend
docker-compose up --build

# In another terminal, run migrations
make migrate
```

### Frontend Only

```bash
cd devintel-frontend
npm install
npm run dev
```

---

## 🐛 Troubleshooting

### Backend Issues

**Problem**: "Docker is not running"
- **Solution**: Start Docker Desktop and wait for it to fully initialize

**Problem**: "Port 8000 already in use"
- **Solution**: Stop any existing backend services or change the port in `docker-compose.yml`

**Problem**: ".env file not found"
- **Solution**: Copy `.env.example` to `.env` and add your API keys

### Frontend Issues

**Problem**: "Port 8080 already in use"
- **Solution**: Stop any existing dev servers or change the port in `vite.config.ts`

**Problem**: "Module not found" errors
- **Solution**: Delete `node_modules` and run `npm install` again

### Database Issues

**Problem**: "Database connection failed"
- **Solution**: Ensure PostgreSQL container is running with `docker ps`
- **Solution**: Check `.env` for correct `DATABASE_URL`

---

## 📖 Next Steps

1. **Configure GitHub OAuth**:
   - Create OAuth App at https://github.com/settings/developers
   - Set callback URL to `http://localhost:8000/auth/github/callback`
   - Add credentials to backend `.env`

2. **Test the Application**:
   - Visit http://localhost:8080
   - Click "Sign in with GitHub"
   - Connect a repository
   - Start chatting with your codebase!

3. **Read the Documentation**:
   - Main README: [README.md](./README.md)
   - Backend docs: [devintel-backend/README.md](./devintel-backend/README.md)
   - Frontend docs: [devintel-frontend/README.md](./devintel-frontend/README.md)

---

## 💡 Tips

- Both services must be running for the application to work
- Backend takes ~30 seconds to fully start
- Frontend hot-reloads on code changes
- Check `/docs` endpoint for interactive API documentation
- Use the stop script to gracefully shutdown all services

---

## 🆘 Getting Help

- Check the [main README](./README.md) for architecture details
- Review backend [README](./devintel-backend/README.md) for API documentation
- Review frontend [README](./devintel-frontend/README.md) for UI components
- Open an issue on GitHub for bugs or questions

---

**Happy Coding! 🚀**
