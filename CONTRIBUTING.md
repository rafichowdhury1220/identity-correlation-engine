# Contributing to Identity Correlation Engine

Thank you for your interest in contributing! This document outlines how to contribute to the project.

## Code of Conduct

Be respectful and professional. We are committed to providing a welcoming environment for everyone.

## Getting Started

### Prerequisites
- Python 3.9+
- Git
- pip / virtualenv

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/identity-correlation-engine.git
cd identity-correlation-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_engine.py -v

# Run with coverage
pytest tests/ --cov=src/identity_engine --cov-report=html
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with Flake8
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/

# Security check
bandit -r src/
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b bugfix/issue-description
```

### 2. Make Changes

- Write clean, well-documented code
- Follow PEP 8 style guide
- Add type hints where possible
- Write docstrings for public functions/classes

### 3. Write Tests

- Add unit tests for new features
- Ensure all tests pass
- Aim for >80% code coverage

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new matching strategy" 
# or 
git commit -m "fix: handle edge case in normalization"
```

**Commit message conventions:**
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for test additions
- `refactor:` for code refactoring
- `perf:` for performance improvements

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create a Pull Request with:
- Clear title describing the change
- Description of what changed and why
- Reference to related issues (if any)
- Screenshots/examples (if applicable)

## PR Review Process

1. **Automated Checks**
   - All tests must pass
   - Code coverage shouldn't decrease
   - Code quality checks (linting, type checking)

2. **Code Review**
   - At least one maintainer review
   - Address feedback and update PR
   - Approval required before merge

3. **Merge**
   - Squash and merge to main
   - Delete feature branch

## Adding New Features

### Adding a New Source Extractor

1. Create `src/identity_engine/extractors/new_source.py`
2. Implement `BaseExtractor` abstract class
3. Add configuration example to `config/`
4. Add tests to `tests/`
5. Update documentation

### Adding a New Matching Strategy

1. Create method in `identity_engine/matchers.py`
2. Inherit from `BaseMatcher`
3. Implement `match()` method
4. Update `HybridMatcher` to use new strategy
5. Add configuration and tests

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design decisions
- Add docstrings to new functions
- Include examples where appropriate

## Reporting Issues

### Security Issues
**Do not** open public issues for security vulnerabilities. Email security@example.com instead.

### Bug Reports
Include:
- Reproduction steps
- Expected behavior
- Actual behavior
- Environment details (Python version, OS)
- Error logs/stack traces

### Feature Requests
- Clear description of the feature
- Use cases and examples
- Why this would be valuable
- Potential implementation approach

## Questions?

- Open an issue with the `question` label
- Check existing discussions
- Review documentation first

---

**Thank you for contributing to Identity Correlation Engine! 🙏**
