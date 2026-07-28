#!/bin/sh
set -e

echo "=== DevIntel startup ==="

# Alembic migrations — env.py handles auto-stamping when tables exist
# but alembic_version tracking is lost (Render free-tier DB recycling).
echo "Running alembic upgrade head..."
alembic upgrade head
echo "Migrations complete!"

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
