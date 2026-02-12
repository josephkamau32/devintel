# Monitoring & Observability Setup

## Overview

This guide helps you set up comprehensive monitoring for DevIntel using industry-standard tools.

---

## Quick Setup: Sentry (Error Tracking)

### 1. Create Sentry Account

1. Go to [sentry.io](https://sentry.io) and sign up
2. Create new project → Python (FastAPI)
3. Copy your DSN: `https://xxxxx@xxxxxx.ingest.sentry.io/xxxxxx`

### 2. Install Sentry SDK

```bash
cd devintel-backend
poetry add sentry-sdk[fastapi]
```

### 3. Configure Sentry

**Update `app/main.py`:**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings

# Initialize Sentry
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Don't send sensitive data
        send_default_pii=False,
        before_send=filter_sensitive_data,
    )

def filter_sensitive_data(event, hint):
    """Remove sensitive information from Sentry events."""
    # Remove Authorization headers
    if 'request' in event and 'headers' in event['request']:
        event['request']['headers'].pop('Authorization', None)
        event['request']['headers'].pop('Cookie', None)
    
    # Remove sensitive query parameters
    if 'request' in event and 'query_string' in event['request']:
        # Parse and filter query parameters
        pass
    
    return event
```

### 4. Add Environment Variables

```env
SENTRY_DSN=https://xxxxx@xxxxxx.ingest.sentry.io/xxxxxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of requests
```

### 5. Test Sentry

```python
# Add test endpoint (development only)
@app.get("/debug/sentry")
async def trigger_error():
    if settings.environment == "development":
        division_by_zero = 1 / 0
    return {"message": "Endpoint disabled in production"}
```

Visit `/debug/sentry` and check Sentry dashboard for error.

### 6. Sentry Alerts

Configure alerts in Sentry dashboard:
- Email on new issue
- Slack integration for critical errors
- Weekly digest of errors

---

## Uptime Monitoring

### Option 1: UptimeRobot (Free)

1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://api.yourdomain.com/health`
   - **Interval**: 5 minutes
   - **Alert contacts**: Your email

3. Configure health check endpoint:

```python
@app.get("/health")
async def health_check():
    """Health check with database ping."""
    try:
        # Check database
        async with get_db() as db:
            await db.execute("SELECT 1")
        
        # Check Redis
        redis_ok = await redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "devintel-ai",
            "database": "ok",
            "redis": "ok" if redis_ok else "error",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }, 503
```

### Option 2: Better Uptime (More Features)

Similar setup to UptimeRobot but with:
- Status pages
- Incident management
- On-call scheduling

---

## Application Metrics

### Prometheus + Grafana Stack

#### 1. Add Prometheus Exporter

```bash
poetry add prometheus-fastapi-instrumentator
```

**Update `app/main.py`:**

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)

# Instrument FastAPI with Prometheus
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

#### 2. Deploy Prometheus (Docker)

**Create `prometheus.yml`:**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'devintel-api'
    static_configs:
      - targets: ['api:8000']
```

**Update `docker-compose.prod.yml`:**

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

#### 3. Grafana Dashboard

1. Visit `http://localhost:3000` (admin/admin)
2. Add Prometheus data source: `http://prometheus:9090`
3. Import dashboard ID `14783` (FastAPI Observability)

**Key Metrics to Monitor:**
- Request rate (requests/second)
- Response time (P50, P95, P99)
- Error rate (5xx responses)
- CPU and memory usage
- Database connection pool size

---

## Logging

### Structured JSON Logging

**Update `app/core/logging.py`:**

```python
import logging
import json
from datetime import datetime
from typing import Any

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging():
    """Configure logging for production."""
    formatter = JSONFormatter() if settings.log_format == "json" else logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    logging.root.setLevel(settings.log_level)
    logging.root.addHandler(handler)
```

### Log Aggregation (Optional)

For production, use one of:

**Option 1: Cloud Watch (AWS)**
- Automatic with ECS/Fargate
- Queryable logs
- Metric filters

**Option 2: Elasticsearch + Kibana (ELK)**
- Self-hosted or managed (Elastic Cloud)
- Powerful querying
- Expensive at scale

**Option 3: Papertrail (Simple)**
- Easy setup
- Free tier: 50MB/month
- Searchable

---

## Performance Monitoring

### Database Query Monitoring

**Add slow query logging:**

```python
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Log slow queries (> 100ms)
    if total > 0.1:
        logger.warning(
            f"Slow query detected: {total:.2f}s",
            extra={
                "query": statement,
                "duration": total,
            }
        )
```

### APM (Application Performance Monitoring)

**Option 1: Datadog (Expensive but Powerful)**
```bash
poetry add ddtrace
ddtrace-run python -m uvicorn app.main:app
```

**Option 2: New Relic**
```bash
pip install newrelic
newrelic-admin run-program python -m uvicorn app.main:app
```

---

## Custom Business Metrics

Track application-specific metrics:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
chat_requests_total = Counter(
    'chat_requests_total',
    'Total number of chat requests',
    ['repository', 'status']
)

chat_duration = Histogram(
    'chat_duration_seconds',
    'Time spent processing chat requests'
)

repositories_indexed = Gauge(
    'repositories_indexed_total',
    'Total number of indexed repositories'
)

# Use in code
@router.post("/chat")
async def chat(request: ChatRequest):
    with chat_duration.time():
        # ... process chat ...
        chat_requests_total.labels(
            repository=request.repository_id,
            status='success'
        ).inc()
```

---

## Alerting Rules

### Critical Alerts (Page immediately)

- API is down (health check fails)
- Error rate > 5%
- Database connection pool exhausted
- Disk space < 10%

### Warning Alerts (Notify, don't page)

- Response time P95 > 1s
- Error rate > 1%
- Memory usage > 80%
- Celery queue backlog > 100

### Info Alerts (Log only)

- New deployment
- Scaling event
- Configuration change

---

## Monitoring Dashboard

Create a single dashboard showing:

```
┌─────────────────────────────────────────┐
│         System Health Overview          │
├─────────────────────────────────────────┤
│ API Status: ✅ Healthy                  │
│ DB Status:  ✅ Healthy                  │
│ Redis:      ✅ Healthy                  │
│ Workers:    ✅ 3/3 Running              │
├─────────────────────────────────────────┤
│         Request Metrics (24h)           │
│ Total Requests:     125,432             │
│ Error Rate:         0.2%                │
│ Avg Response Time:  85ms                │
│ P95 Response Time:  320ms               │
├─────────────────────────────────────────┤
│         Business Metrics                │
│ Active Users:       1,245               │
│ Repositories:       8,932               │
│ Chat Messages:      45,678              │
│ Avg Indexing Time:  28s                 │
└─────────────────────────────────────────┘
```

---

## Cost Optimization

Free tier options:
- **Sentry**: 5,000 events/month
- **UptimeRobot**: 50 monitors
- **Grafana Cloud**: 10k metrics
- **Papertrail**: 50MB logs/month

Total cost: $0-20/month for small scale

---

## Checklist

- [ ] Sentry configured and tested
- [ ] Uptime monitoring active
- [ ] Health check endpoint working
- [ ] Structured logging implemented
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboard created
- [ ] Alert rules configured
- [ ] On-call rotation defined (if team)
- [ ] Runbook created for common issues

---

Last updated: 2026-02-12
