# ============================================
# DevIntel - Stop Script (Windows PowerShell)
# ============================================
# This script stops all running DevIntel services

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DevIntel AI - Stopping Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the root directory
$ROOT_DIR = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT_DIR "devintel-backend"

# ============================================
# Stop Backend Docker Containers
# ============================================
Write-Host "🛑 Stopping Backend Services..." -ForegroundColor Yellow
Write-Host ""

Set-Location $BACKEND_DIR

try {
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Backend services stopped" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Warning: Could not stop backend services (may not be running)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Warning: Docker may not be running" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# Kill Frontend Process
# ============================================
Write-Host "🛑 Stopping Frontend Server..." -ForegroundColor Yellow
Write-Host ""

# Find and kill Node processes running Vite
try {
    $viteProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*vite*"
    }
    
    if ($viteProcesses) {
        $viteProcesses | Stop-Process -Force
        Write-Host "✓ Frontend server stopped" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  No frontend server found (may not be running)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Could not stop frontend (may not be running)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# Summary
# ============================================
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ All Services Stopped" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Return to root directory
Set-Location $ROOT_DIR

Write-Host "Press any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
