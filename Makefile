.PHONY: help dev test lint typecheck build deploy openapi clean

help:			## Show available commands
	@echo "DevIntel AI — Monorepo Commands"
	@echo "──────────────────────────────────────────"
	@echo "dev          Start all services for development"
	@echo "test         Run all tests (backend + frontend)"
	@echo "lint         Lint all code (ruff + eslint)"
	@echo "typecheck    Run type checkers (mypy)"
	@echo "build        Build production artifacts"
	@echo "deploy       Deploy to production (Docker Compose)"
	@echo "openapi      Export OpenAPI schema"
	@echo "clean        Remove caches and temp files"

dev:			## Start all services for development
	cd devintel-backend && docker-compose up --build

test:			## Run all tests
	cd devintel-backend && pytest tests/ -v --cov=app --cov-report=term-missing
	cd devintel-frontend && npm run test -- --run

lint:			## Lint all code
	cd devintel-backend && ruff check app/
	cd devintel-frontend && npm run lint

typecheck:		## Run type checkers
	cd devintel-backend && mypy app/ --ignore-missing-imports

build:			## Build production artifacts
	cd devintel-frontend && npm run build
	cd devintel-backend && docker build -t devintel-backend .

deploy:			## Deploy to production
	docker compose -f docker-compose.prod.yml up -d --build

openapi:		## Export OpenAPI schema
	cd devintel-backend && python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > devintel-backend/docs/openapi.json

clean:			## Remove caches and temp files
	cd devintel-backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd devintel-backend && find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	cd devintel-backend && find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	cd devintel-backend && find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	cd devintel-frontend && rm -rf dist/ node_modules/.cache/
