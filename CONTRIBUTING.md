# Contributing to XnoxsFetcher

First off, thank you for considering contributing to XnoxsFetcher! It's people like you that make XnoxsFetcher such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

- Make sure you have a [GitHub account](https://github.com/signup)
- Fork the repository on GitHub
- Clone your fork locally
- Set up the development environment (see below)

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, screenshots)
- **Describe the behavior you observed and expected**
- **Include your environment details** (OS, Python version, package version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List any alternatives you've considered**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the style guidelines
6. Issue the pull request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip or uv package manager
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/xnoxs_fetcher.git
cd xnoxs_fetcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xnoxs_fetcher --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run tests with verbose output
pytest -v
```

### Code Quality Tools

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy xnoxs_fetcher/

# Fix auto-fixable issues
ruff check --fix .
```

## Style Guidelines

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters maximum
- **Imports**: Organized by isort (handled by ruff)
- **Formatting**: Black-compatible (handled by ruff)
- **Type hints**: Required for all public functions

### Code Quality

- Write docstrings for all public classes, methods, and functions
- Use type hints consistently
- Keep functions small and focused
- Write meaningful variable names
- Add comments for complex logic

### Documentation Style

- Use Google-style docstrings
- Include examples in docstrings where helpful
- Keep README and docs up to date

Example:

```python
def fetch_data(
    symbol: str,
    exchange: str,
    timeframe: TimeFrame,
    n_bars: int = 100
) -> pd.DataFrame:
    """Fetch historical market data for a symbol.

    Args:
        symbol: The trading symbol (e.g., "AAPL", "BTCUSD").
        exchange: The exchange name (e.g., "NASDAQ", "BINANCE").
        timeframe: The data timeframe/interval.
        n_bars: Number of bars to fetch. Defaults to 100.

    Returns:
        DataFrame with OHLCV data indexed by datetime.

    Raises:
        ValueError: If symbol or exchange is invalid.
        ConnectionError: If unable to connect to TradingView.

    Example:
        >>> fetcher = XnoxsFetcher()
        >>> df = fetcher.fetch_data("AAPL", "NASDAQ", TimeFrame.D1)
        >>> print(df.head())
    """
```

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system or dependency changes
- `ci`: CI/CD configuration changes
- `chore`: Other changes that don't modify src or test files

### Examples

```
feat(auth): add session persistence with JSON storage

fix(websocket): handle connection timeout gracefully

docs(readme): update installation instructions

test(parallel): add tests for concurrent fetching
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/my-new-feature
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   ruff format .
   ruff check .
   mypy xnoxs_fetcher/
   pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add awesome new feature"
   ```

5. **Push to your fork**
   ```bash
   git push origin feat/my-new-feature
   ```

6. **Open a Pull Request**
   - Fill out the PR template
   - Link any related issues
   - Request review from maintainers

7. **Address review feedback**
   - Make requested changes
   - Push additional commits
   - Re-request review when ready

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉
