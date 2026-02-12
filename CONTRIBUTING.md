# Contributing to DevIntel AI

First off, thank you for considering contributing to DevIntel AI! It's people like you that make DevIntel such a great tool for developers worldwide.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to conduct@devintel.ai.

**TL;DR**: Be kind, respectful, and professional.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, screenshots)
- **Describe the observed behavior** and what you expected
- **Include your environment** (OS, Python version, Node version)  

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

- **Use a clear and descriptive title**
- **Provide a detailed description of the proposed enhancement**
- **Explain why this enhancement would be useful**
- **Include mockups or examples if applicable**

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:

- `good first issue` - Simple issues perfect for beginners
- `help wanted` - Issues where we need community help
- `documentation` - Documentation improvements

## Development Setup

### Prerequisites

- **Docker & Docker Compose** (required)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend)
- **Git**

### Setup Steps

1. **Fork the repository**

   Click the "Fork" button on GitHub

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR-USERNAME/devintel.git
   cd devintel
   ```

3. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/josephkamau32/devintel.git
   ```

4. **Set up environment** files

   ```bash
   # Backend
   cd devintel-backend
   cp .env.example .env
   # Edit .env with your API keys

   # Frontend
   cd ../devintel-frontend
   cp .env.example .env
   ```

5. **Start development environment**

   ```bash
   # From project root
   ./scripts/start.ps1  # Windows
   # OR
   ./scripts/start.sh  # Linux/Mac
   ```

6. **Verify setup**

   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:8080  
   - Database is running in Docker

## Development Workflow

### Creating a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# OR
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests

### Making Changes

1. **Write code** following our style guidelines
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run tests locally** to ensure everything works
5. **Commit your changes** with clear messages

### Committing

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add user preferences endpoint"
git commit -m "fix: resolve chat streaming issue"
git commit -m "docs: update API documentation"
git commit -m "test: add tests for authentication"
```

Commit types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style changes (formatting)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

## Code Style Guidelines

### Backend (Python)

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
# Auto-format code
make format

# Run linter
make lint

# Type check
make typecheck
```

**Code standards:**
- Follow PEP 8
- Use type hints for all functions
- Write Google-style docstrings
- Maximum line length: 100 characters
- Use async/await for I/O operations

**Example:**

```python
async def get_user_by_id(user_id: UUID) -> Optional[User]:
    """
    Retrieve a user by their ID.
    
    Args:
        user_id: The unique identifier of the user
    
    Returns:
        User object if found, None otherwise
    
    Raises:
        DatabaseError: If database query fails
    """
    ...
```

### Frontend (TypeScript/React)

We use:
- **ESLint** for linting
- **Prettier** for formatting

```bash
# Run linter
npm run lint

# Auto-fix issues
npm run lint:fix
```

**Code standards:**
- Use TypeScript strict mode
- Prefer functional components
- Use React hooks properly
- Export named components
- Write JSDoc for complex functions

**Example:**

```typescript
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ userId, onUpdate }) => {
  // Component implementation
};
```

## Testing Requirements

### All contributions must include tests!

#### Backend Tests

- **Unit tests** for new functions/classes
- **Integration tests** for API endpoints
- **Maintain >80% coverage**

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_api/test_auth.py -v
```

#### Frontend Tests

- **Component tests** for new UI components
- **Hook tests** for custom hooks
- **Integration tests** for critical flows

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch
```

### Test Guidelines

- **Write descriptive test names**
- **Test edge cases and error conditions**
- **Use fixtures and mocks appropriately**
- **Keep tests fast and isolated**
- **One assertion per test (when possible)**

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No merge conflict with main branch
- [ ] Commit messages follow conventions

### Submitting a PR

1. **Push your branch**

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub

3. **Fill out the PR template** completely

4. **Link related issues** using keywords:
   - `Fixes #123`
   - `Closes #456`
   - `Relates to #789`

### PR Title Format

```
type(scope): brief description

Example:
feat(auth): add OAuth2 token refresh
fix(chat): resolve streaming response issue
docs(readme): add installation instructions
```

### PR Description Should Include

- **What**: What does this PR do?
- **Why**: Why is this change needed?
- **How**: How does it work?
- **Testing**: How was it tested?
- **Screenshots**: If UI changes

### Review Process

- At least one maintainer will review your PR
- Address review comments promptly
- Update your PR based on feedback
- Once approved, a maintainer will merge

### After Merge

```bash
# Update your local main
git checkout main
git pull upstream main

# Delete your feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## Community

### Getting Help

- **GitHub Discussions** - Ask questions, share ideas
- **Issue Tracker** -Report bugs
- **Email** - support@devintel.ai

### Stay Updated

- Watch the repository for updates
- Read the changelog for new releases
- Follow us on social media (coming soon)

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project website (coming soon)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to DevIntel AI!** 🚀

Your efforts help make developer productivity tools better for everyone.
