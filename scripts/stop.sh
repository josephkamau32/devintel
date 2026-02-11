#!/bin/bash
# ============================================
# DevIntel - Stop Script (Linux/Mac)
# ============================================
# This script stops all running DevIntel services

echo ""
echo "========================================"
echo "  DevIntel AI - Stopping Services"
echo "========================================"
echo ""

# Get the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/devintel-backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# Stop Backend Docker Containers
# ============================================
echo -e "${YELLOW}🛑 Stopping Backend Services...${NC}"
echo ""

cd "$BACKEND_DIR"

if docker-compose down > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend services stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Could not stop backend services (may not be running)${NC}"
fi

echo ""

# ============================================
# Kill Frontend Process
# ============================================
echo -e "${YELLOW}🛑 Stopping Frontend Server...${NC}"
echo ""

# Find and kill Node processes running Vite
if pkill -f "vite" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend server stopped${NC}"
else
    echo -e "${YELLOW}⚠️  No frontend server found (may not be running)${NC}"
fi

echo ""

# ============================================
# Summary
# ============================================
echo "========================================"
echo -e "${GREEN}  ✓ All Services Stopped${NC}"
echo "========================================"
echo ""

# Return to root directory
cd "$ROOT_DIR"
