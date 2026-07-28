#!/bin/sh
set -e

echo "=== DevIntel startup ==="

# Step 1: Detect DB state and stamp at head if tables exist without Alembic tracking.
# This prevents DuplicateTableError when Render's free-tier DB loses the alembic_version
# table but keeps the app tables (or when create_all in lifespan created them).
echo "Checking database state..."
PYTHONPATH=. python scripts/prepare_db.py

# Step 2: Run any pending Alembic migrations.
echo "Running alembic upgrade head..."
alembic upgrade head
echo "Migrations complete!"

# Step 3: Start the application.
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
