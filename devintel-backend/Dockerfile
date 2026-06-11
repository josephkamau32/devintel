# Production Dockerfile for DevIntel Backend

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies to a shared location
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first (before COPY, so files get correct ownership)
RUN useradd -m -u 1000 devintel

# Copy Python dependencies from builder to system-wide location
COPY --from=builder /install /usr/local

# Copy application code and set ownership
COPY --chown=devintel:devintel . .

# Make sure scripts are executable
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Switch to non-root user
USER devintel

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run database migrations and start application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
