# Development Guide

This document covers the development workflow and code quality tools for the RAG chatbot project.

## Code Quality Tools

This project uses several tools to maintain code quality:

- **Black**: Code formatter (line length: 88)
- **isort**: Import sorter (compatible with Black)
- **flake8**: Linter for style guide enforcement
- **mypy**: Static type checker
- **pytest**: Testing framework with coverage reporting

## Quick Start

### Format Code Automatically

```bash
./format.sh
```

This will:
1. Sort imports with isort
2. Format code with Black

**Always run this before committing!**

### Run Quality Checks

```bash
./quality.sh
```

This runs all checks in sequence:
1. Black formatting check
2. isort import order check
3. flake8 linting
4. mypy type checking
5. pytest with coverage

### Individual Tool Usage

```bash
# Format code
uv run black backend/ main.py

# Sort imports
uv run isort backend/ main.py

# Lint code
uv run flake8 backend/ main.py

# Type check
uv run mypy backend/ main.py

# Run tests with coverage
uv run pytest
```

## Configuration Files

- `pyproject.toml`: Configuration for Black, isort, mypy, pytest, and coverage
- `.flake8`: Flake8 linting rules
- `.pre-commit-config.yaml`: Optional pre-commit hooks

## Optional: Pre-commit Hooks

To automatically run quality checks before each commit:

```bash
# Install pre-commit
uv add --dev pre-commit

# Install the git hooks
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

Once installed, pre-commit will automatically:
- Format code with Black
- Sort imports with isort
- Check for common issues (trailing whitespace, large files, etc.)

## Code Style Guidelines

### Formatting

- Line length: 88 characters (Black default)
- Imports sorted alphabetically and grouped (isort)
- Consistent quote style

### Type Hints

While not strictly enforced (`disallow_untyped_defs = false`), type hints are encouraged for:
- Public API functions
- Complex function signatures
- Return types that aren't obvious

### Imports

Order (managed by isort):
1. Standard library imports
2. Third-party imports
3. Local application imports

### Documentation

- Docstrings for all public classes and functions
- Clear variable names (avoid single letters except in loops)
- Comments for complex logic

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest backend/tests/test_ai_generator.py

# Run with coverage report
uv run pytest --cov=backend --cov-report=html
```

### Coverage Reports

After running tests with coverage:
- Terminal report: Displayed immediately
- HTML report: Open `htmlcov/index.html` in browser

Target: Maintain >80% code coverage

## Continuous Integration

Before pushing code, ensure:
1. All tests pass: `uv run pytest`
2. Code is formatted: `./format.sh`
3. All quality checks pass: `./quality.sh`

## Troubleshooting

### Import Errors

```bash
# Sync dependencies
uv sync
```

### Type Check Failures

If mypy reports errors you want to ignore temporarily, add a comment:
```python
result = some_function()  # type: ignore
```

### Formatting Conflicts

If Black and flake8 disagree, Black takes precedence. The `.flake8` config is already set to ignore Black-incompatible rules (E203, W503).

### Pre-commit Hook Issues

```bash
# Update hooks to latest versions
uv run pre-commit autoupdate

# Clear cache and reinstall
uv run pre-commit clean
uv run pre-commit install
```

## Editor Integration

### VS Code

Install extensions:
- Python (Microsoft)
- Black Formatter
- isort
- Flake8
- Mypy Type Checker

Add to `.vscode/settings.json`:
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. Settings → Tools → Black → Enable
2. Settings → Tools → File Watchers → Add isort
3. Settings → Editor → Inspections → Enable flake8
4. Settings → Editor → Inspections → Enable mypy

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
