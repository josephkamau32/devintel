# ============================================
# DevIntel - Startup Script (Windows PowerShell)
# ============================================
# This script starts both the backend and frontend servers

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DevIntel AI - Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the root directory
$ROOT_DIR = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT_DIR "devintel-backend"
$FRONTEND_DIR = Join-Path $ROOT_DIR "devintel-frontend"

# Check if directories exist
if (-not (Test-Path $BACKEND_DIR)) {
    Write-Host "❌ Error: Backend directory not found at $BACKEND_DIR" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "❌ Error: Frontend directory not found at $FRONTEND_DIR" -ForegroundColor Red
    exit 1
}

# ============================================
# Step 1: Start Backend
# ============================================
Write-Host "📦 Step 1/3: Starting Backend Services" -ForegroundColor Yellow
Write-Host "Location: $BACKEND_DIR" -ForegroundColor Gray
Write-Host ""

# Check if .env file exists
if (-not (Test-Path (Join-Path $BACKEND_DIR ".env"))) {
    Write-Host "⚠️  Warning: .env file not found in backend directory" -ForegroundColor Yellow
    Write-Host "   Creating from .env.example..." -ForegroundColor Gray
    
    if (Test-Path (Join-Path $BACKEND_DIR ".env.example")) {
        Copy-Item (Join-Path $BACKEND_DIR ".env.example") (Join-Path $BACKEND_DIR ".env")
        Write-Host "   ✓ Created .env file" -ForegroundColor Green
        Write-Host "   ⚠️  Please update .env with your API keys!" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "   ❌ .env.example not found. Please create .env manually." -ForegroundColor Red
        exit 1
    }
}

# Start backend with Docker Compose
Set-Location $BACKEND_DIR
Write-Host "Starting Docker containers..." -ForegroundColor Gray

# Check if Docker is running
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running"
    }
} catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Start backend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BACKEND_DIR'; docker-compose up --build"

Write-Host "✓ Backend starting in new window..." -ForegroundColor Green
Write-Host "  API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Wait for backend to be ready
Write-Host "Waiting for backend to start (30 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 30

# ============================================
# Step 2: Start Frontend
# ============================================
Write-Host "📦 Step 2/3: Starting Frontend Development Server" -ForegroundColor Yellow
Write-Host "Location: $FRONTEND_DIR" -ForegroundColor Gray
Write-Host ""

Set-Location $FRONTEND_DIR

# Check if node_modules exists
if (-not (Test-Path (Join-Path $FRONTEND_DIR "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Start frontend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FRONTEND_DIR'; npm run dev"

Write-Host "✓ Frontend starting in new window..." -ForegroundColor Green
Write-Host "  App: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""

# ============================================
# Step 3: Summary
# ============================================
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ All Services Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://localhost:8080" -ForegroundColor White
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   • Both servers are running in separate PowerShell windows" -ForegroundColor Gray
Write-Host "   • Press Ctrl+C in each window to stop the servers" -ForegroundColor Gray
Write-Host "   • Or run: .\scripts\stop.ps1 to stop all services" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 For more information, see README.md" -ForegroundColor Cyan
Write-Host ""

# Return to root directory
Set-Location $ROOT_DIR

# Keep this window open
Write-Host "Press any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
