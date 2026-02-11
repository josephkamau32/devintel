.PHONY: help dev build up down logs shell test lint format typecheck migrate migration clean

help:
	@echo "DevIntel AI Backend - Available Commands"
	@echo "----------------------------------------"
	@echo "dev          - Start all services for development"
	@echo "build        - Build Docker images"
	@echo "up           - Start services in detached mode"
	@echo "down         - Stop all services"
	@echo "logs         - View logs from all services"
	@echo "shell        - Open shell in API container"
	@echo "test         - Run tests"
	@echo "test-cov     - Run tests with coverage"
	@echo "lint         - Run linter (ruff)"
	@echo "format       - Format code (black)"
	@echo "typecheck    - Run type checker (mypy)"
	@echo "migrate      - Run database migrations"
	@echo "migration    - Create new migration (use name='description')"
	@echo "clean        - Remove temporary files and caches"

dev:
	docker-compose up --build

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec api /bin/bash

test:
	docker-compose exec api pytest

test-cov:
	docker-compose exec api pytest --cov=app --cov-report=html --cov-report=term

lint:
	docker-compose exec api ruff check app/

format:
	docker-compose exec api black app/

typecheck:
	docker-compose exec api mypy app/

migrate:
	docker-compose exec api alembic upgrade head

migration:
	@if [ -z "$(name)" ]; then \
		echo "Error: Please specify a migration name. Usage: make migration name='description'"; \
		exit 1; \
	fi
	docker-compose exec api alembic revision --autogenerate -m "$(name)"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
