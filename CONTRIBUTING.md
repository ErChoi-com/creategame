# Contributing to Kronos Crypto Price Trend Prediction

Thank you for your interest in contributing to Kronos! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project follows a Code of Conduct that all contributors are expected to adhere to. Please be respectful, inclusive, and professional in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/kronos-crypto.git`
3. Add upstream remote: `git remote add upstream https://github.com/original-repo/kronos-crypto.git`
4. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or poetry
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/kronos-crypto.git
cd kronos-crypto

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Development Dependencies

The `[dev]` extra includes:
- `pytest` - Testing framework
- `black` - Code formatter
- `flake8` - Linter
- `mypy` - Type checker
- `isort` - Import sorter

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

1. **Bug Fixes** - Fix issues in the codebase
2. **Feature Additions** - Add new functionality
3. **Documentation** - Improve docs, add examples
4. **Tests** - Add or improve test coverage
5. **Performance** - Optimize slow operations
6. **Code Quality** - Refactoring, type hints, etc.

### Workflow

1. **Find or create an issue** - Check existing issues or create a new one
2. **Discuss the approach** - Comment on the issue to discuss your approach
3. **Fork and branch** - Fork the repo and create a feature branch
4. **Make changes** - Implement your changes following coding standards
5. **Test** - Ensure all tests pass and add new tests if needed
6. **Commit** - Write clear, descriptive commit messages
7. **Push** - Push your changes to your fork
8. **Pull Request** - Open a PR with a clear description

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Write docstrings for all modules, classes, and functions (Google style)
- Keep line length ≤ 100 characters
- Use meaningful variable and function names

### Code Formatting

We use `black` for code formatting:

```bash
# Format all code
black src/

# Check without modifying
black --check src/
```

### Import Sorting

We use `isort` for import organization:

```bash
# Sort imports
isort src/

# Check without modifying
isort --check src/
```

### Type Checking

We use `mypy` for static type checking:

```bash
# Run type checker
mypy src/
```

### Linting

We use `flake8` for linting:

```bash
# Run linter
flake8 src/
```

### Example Function

```python
from typing import Dict, List, Optional
import pandas as pd


def process_data(
    df: pd.DataFrame,
    config: Dict,
    symbols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Process cryptocurrency data according to configuration.

    Args:
        df: Input DataFrame with OHLCV data
        config: Configuration dictionary with processing parameters
        symbols: Optional list of symbols to filter. If None, process all.

    Returns:
        Processed DataFrame with additional columns

    Raises:
        ValueError: If DataFrame is empty or missing required columns

    Example:
        >>> df = pd.DataFrame({'close': [100, 101, 102]})
        >>> config = {'window': 10}
        >>> result = process_data(df, config)
    """
    if df is None or len(df) == 0:
        raise ValueError("DataFrame cannot be empty")

    # Implementation here
    return df
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_data_ingest.py

# Run specific test
pytest tests/test_data_ingest.py::test_fetch_klines
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common setup

Example test:

```python
import pytest
from src.data_ingest import BinanceDataFetcher


def test_interval_to_milliseconds():
    """Test interval conversion to milliseconds."""
    fetcher = BinanceDataFetcher(mock_config)

    assert fetcher._interval_to_milliseconds("1m") == 60_000
    assert fetcher._interval_to_milliseconds("1h") == 3_600_000
    assert fetcher._interval_to_milliseconds("1d") == 86_400_000

    with pytest.raises(ValueError):
        fetcher._interval_to_milliseconds("1x")
```

## Pull Request Process

### Before Submitting

1. **Update documentation** - Update README, docstrings, comments
2. **Add tests** - Ensure new code is tested
3. **Run all checks** - Formatting, linting, type checking, tests
4. **Update changelog** - Add entry to CHANGELOG.md
5. **Rebase on main** - Ensure your branch is up-to-date

### PR Template

When opening a PR, include:

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings

## Testing
Describe how you tested these changes

## Related Issues
Fixes #123
```

### Review Process

1. **Automated checks** - CI/CD will run tests and linters
2. **Code review** - Maintainers will review your code
3. **Address feedback** - Make requested changes
4. **Approval** - Once approved, maintainers will merge

## Reporting Bugs

### Before Reporting

- Check existing issues
- Try the latest version
- Collect relevant information

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## To Reproduce
Steps to reproduce:
1. Run command '...'
2. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- Package version: [e.g., 1.0.0]

## Logs/Screenshots
Relevant logs or screenshots

## Additional Context
Any other relevant information
```

## Suggesting Enhancements

### Enhancement Template

```markdown
## Feature Description
Clear description of the proposed feature

## Motivation
Why is this feature needed?

## Proposed Solution
How should this be implemented?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other relevant information
```

## Areas for Contribution

### High Priority

- Additional data sources (Coinbase, Kraken, etc.)
- More technical indicators
- Deep learning models (LSTM, Transformers)
- Live trading integration (with appropriate warnings)
- Performance optimizations
- Expanded test coverage

### Documentation

- Tutorial videos or blog posts
- Jupyter notebook examples
- API documentation improvements
- Translation to other languages

### Tools & Infrastructure

- Docker containerization
- CI/CD improvements
- Monitoring and alerting
- Deployment scripts

## Questions?

If you have questions:

1. Check existing issues and discussions
2. Review documentation
3. Ask in discussions tab
4. Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Annual contribution reports

Thank you for contributing to Kronos! 🚀
