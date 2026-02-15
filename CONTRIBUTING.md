# Contributing to DevIntel

Thank you for your interest in contributing to DevIntel! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/devintel.git
   cd devintel
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Backend
```bash
cd devintel-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your environment
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd devintel-frontend
npm install
npm run dev
```

### Docker (Recommended)
```bash
docker-compose up
```

## Making Changes

### Code Style

**Backend (Python)**:
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Run `black` for formatting
- Run `ruff` for linting

**Frontend (TypeScript)**:
- Follow ESLint configuration
- Use TypeScript strict mode
- Functional components with hooks
- Run `npm run lint`

### Testing

**Backend**:
```bash
pytest tests/ -v --cov=app --cov-report=html
```

**Frontend**:
```bash
npm run test
npm run test:coverage
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user profile endpoint
fix: resolve CORS issue in production
docs: update API documentation
test: add tests for chat service
refactor: extract constants from config
```

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update CHANGELOG.md**
5. **Create pull request** with description

### PR Title Format
```
[Type] Brief description
```
Examples:
- `[Feature] Add GitHub token refresh`
- `[Fix] Resolve memory leak in worker`
- `[Docs] Add deployment guide`

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [] Bug fix
- [] New feature
- [] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings
```

## Project Structure

```
devintel/
├── devintel-backend/     # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core utilities
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   └── middleware/   # Middleware
│   ├── tests/            # Test suite
│   └── alembic/          # Database migrations
│
├── devintel-frontend/    # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── lib/          # Utilities
│   │   └── hooks/        # Custom hooks
│   └── tests/            # Test suite
│
└── docs/                 # Documentation
```

## Areas for Contribution

### High Priority
- [ ] Increase test coverage (target: 80%+)
- [ ] Performance optimizations
- [ ] Security improvements
- [ ] Documentation improvements

### Good First Issues
- [ ] Add new file type support for indexing
- [ ] Improve error messages
- [ ] Add loading states
- [ ] Write integration tests

### Advanced Features
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Real-time collaboration
- [ ] Plugin system

## Review Process

1. Maintainer reviews PR
2. Request changes if needed
3. Approval after changes addressed
4. Merge to `main`

## Recognition

Contributors will be added to:
- README.md contributors section
- GitHub contributors page
- Release notes (for significant contributions)

## Questions?

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: contribute@devintel.ai

Thank you for contributing! 🚀
