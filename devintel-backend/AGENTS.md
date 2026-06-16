# Agent Commands

## Lint & Type Check

- **Lint**: `docker-compose exec api ruff check app/`
- **TypeCheck**: `docker-compose exec api mypy app/`
- **Format**: `docker-compose exec api black app/`

## Run Tests

- **Test**: `docker-compose exec api pytest`
- **Test with coverage**: `docker-compose exec api pytest --cov=app --cov-report=html --cov-report=term`

## Database Migrations

- **Apply migrations**: `docker-compose exec api alembic upgrade head`
- **Create migration**: `docker-compose exec api alembic revision --autogenerate -m "description"`