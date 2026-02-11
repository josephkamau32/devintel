#!/bin/bash
# ============================================
# DevIntel - Startup Script (Linux/Mac)
# ============================================
# This script starts both the backend and frontend servers

echo ""
echo "========================================"
echo "  DevIntel AI - Starting Services"
echo "========================================"
echo ""

# Get the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/devintel-backend"
FRONTEND_DIR="$ROOT_DIR/devintel-frontend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Check if directories exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Error: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# ============================================
# Step 1: Start Backend
# ============================================
echo -e "${YELLOW}📦 Step 1/3: Starting Backend Services${NC}"
echo -e "${GRAY}Location: $BACKEND_DIR${NC}"
echo ""

# Check if .env file exists
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found in backend directory${NC}"
    echo -e "${GRAY}   Creating from .env.example...${NC}"
    
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo -e "${GREEN}   ✓ Created .env file${NC}"
        echo -e "${YELLOW}   ⚠️  Please update .env with your API keys!${NC}"
        echo ""
    else
        echo -e "${RED}   ❌ .env.example not found. Please create .env manually.${NC}"
        exit 1
    fi
fi

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running. Please start Docker.${NC}"
    exit 1
fi

# Start backend
cd "$BACKEND_DIR"
echo -e "${GRAY}Starting Docker containers...${NC}"

# Start backend in background
docker-compose up --build > /tmp/devintel-backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✓ Backend starting (PID: $BACKEND_PID)...${NC}"
echo -e "${CYAN}  API: http://localhost:8000${NC}"
echo -e "${CYAN}  Docs: http://localhost:8000/docs${NC}"
echo ""

# Wait for backend to be ready
echo -e "${GRAY}Waiting for backend to start (30 seconds)...${NC}"
sleep 30

# ============================================
# Step 2: Start Frontend
# ============================================
echo -e "${YELLOW}📦 Step 2/3: Starting Frontend Development Server${NC}"
echo -e "${GRAY}Location: $FRONTEND_DIR${NC}"
echo ""

cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${GRAY}Installing frontend dependencies...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: Failed to install frontend dependencies${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
fi

# Start frontend in background
npm run dev > /tmp/devintel-frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}✓ Frontend starting (PID: $FRONTEND_PID)...${NC}"
echo -e "${CYAN}  App: http://localhost:8080${NC}"
echo ""

# ============================================
# Step 3: Summary
# ============================================
echo "========================================"
echo -e "${GREEN}  ✓ All Services Started Successfully!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}🌐 Access Points:${NC}"
echo -e "   Frontend:  http://localhost:8080"
echo -e "   Backend:   http://localhost:8000"
echo -e "   API Docs:  http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "${GRAY}   • Backend PID: $BACKEND_PID${NC}"
echo -e "${GRAY}   • Frontend PID: $FRONTEND_PID${NC}"
echo -e "${GRAY}   • Logs: /tmp/devintel-backend.log & /tmp/devintel-frontend.log${NC}"
echo -e "${GRAY}   • Run: ./scripts/stop.sh to stop all services${NC}"
echo ""
echo -e "${CYAN}📖 For more information, see README.md${NC}"
echo ""

# Return to root directory
cd "$ROOT_DIR"
