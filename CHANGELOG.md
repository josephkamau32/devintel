# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-06-15

### Added
- Production-grade FastAPI backend with async SQLAlchemy
- GitHub OAuth and email/password authentication with JWT tokens
- Tree-sitter AST-aware semantic code chunking
- pgvector integration for PostgreSQL vector similarity search
- RAG-powered chat with streaming SSE responses
- Autonomous agent for PR generation and code fixing
- Auto-fix service with self-correction loop
- Code health analysis with multi-dimensional scoring
- PR review automation with AI suggestions
- VS Code extension with integrated chat sidebar
- Comprehensive security middleware (CSRF, rate limiting, SQL injection detection)
- Prometheus metrics endpoint
- OpenTelemetry-ready structured logging
- Circuit breaker pattern for OpenAI API resilience
- Retry queue for failed indexing tasks
- OpenAPI schema generation

### Security
- Fernet AES-256 encryption for GitHub tokens
- SHA-256 hashed refresh tokens
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Request size limiting
- SQL injection detection middleware

### Infrastructure
- Docker production deployment
- Docker Compose for local development
- CI/CD with GitHub Actions
- Free-tier deployment support (Render + Neon + Vercel)

### Documentation
- Architecture Decision Records (ADRs)
- OpenAPI specification
- Contributing guidelines

## [0.1.0] - 2024-02-11

### Added
- Initial project structure
- Basic FastAPI skeleton
- GitHub OAuth integration
- Repository indexing pipeline