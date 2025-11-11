# Contributing to GitHub Project Manager MCP

First off, thank you for considering contributing to GitHub Project Manager MCP! It's people like you that make it a great tool for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include any error messages or logs
* Include Python version and operating system information

### Suggesting Enhancements

If you have a suggestion for a new feature or enhancement:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful
* Consider the impact on existing functionality

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python styleguide (see below)
* Include thoughtfully-worded, well-structured tests
* Document new code with docstrings
* End all files with a newline
* Ensure all tests pass before submitting
* Run code quality checks (black, ruff, mypy)

## Development Process

1. Fork the repo
2. Create a new branch from `main`: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run the tests: `pytest`
5. Run code quality checks: `black src/`, `ruff check src/`, `mypy src/`
6. Push to your fork: `git push origin feature/amazing-feature`
7. Submit a pull request

### Setup Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/git_proj_manger_mcp.git
cd git_proj_manger_mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m src --version
```

### Running the Server Locally

```bash
# Set up environment variables
export GITHUB_TOKEN=your_token
export GITHUB_OWNER=your_username
export GITHUB_REPO=your_repo

# Or create a .env file
echo "GITHUB_TOKEN=your_token" > .env
echo "GITHUB_OWNER=your_username" >> .env
echo "GITHUB_REPO=your_repo" >> .env

# Run the server
python -m src

# Or with verbose logging
python -m src --verbose
```

## Code Quality

### Formatting

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format all code
black src/

# Check formatting without making changes
black --check src/
```

### Linting

We use [Ruff](https://docs.astral.sh/ruff/) for linting:

```bash
# Lint all code
ruff check src/

# Auto-fix linting issues
ruff check --fix src/
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) for type checking:

```bash
# Type check all code
mypy src/

# Type check specific files
mypy src/infrastructure/tools/
```

### Pre-commit Checks

Before committing, ensure:

1. Code is formatted: `black src/`
2. No linting errors: `ruff check src/`
3. Type checking passes: `mypy src/`
4. All tests pass: `pytest`

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Use conventional commit format when possible:
  * `feat:` for new features
  * `fix:` for bug fixes
  * `docs:` for documentation changes
  * `style:` for formatting changes
  * `refactor:` for code refactoring
  * `test:` for test changes
  * `chore:` for maintenance tasks

Example:
```
feat: Add support for custom project fields

This adds the ability to create and manage custom fields in GitHub Projects.
Includes validation and error handling.

Closes #123
```

### Python Styleguide

We follow [PEP 8](https://peps.python.org/pep-0008/) with some modifications:

* Use 4 spaces for indentation (not tabs)
* Use `snake_case` for variables and functions
* Use `PascalCase` for classes
* Use `UPPER_CASE` for constants
* Use meaningful variable names
* Add type hints for all function parameters and return values
* Document public APIs using docstrings (Google style)
* Maximum line length: 100 characters (Black default)
* Import order: standard library, third-party, local imports

#### Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict, Any

async def create_issue(
    self,
    data: CreateIssue,
    options: Optional[Dict[str, Any]] = None
) -> Issue:
    """Create a new issue.
    
    Args:
        data: Issue creation data
        options: Optional configuration options
        
    Returns:
        Created issue instance
        
    Raises:
        ValidationError: If data is invalid
        GitHubAPIError: If GitHub API call fails
    """
    ...
```

#### Docstrings

Use Google-style docstrings:

```python
def process_data(data: List[str]) -> Dict[str, int]:
    """Process a list of strings and return counts.
    
    Args:
        data: List of strings to process
        
    Returns:
        Dictionary mapping strings to their counts
        
    Raises:
        ValueError: If data is empty
    """
    ...
```

#### Async/Await

Always use async/await for I/O operations:

```python
async def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data from URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Documentation Styleguide

* Use [Markdown](https://guides.github.com/features/mastering-markdown/)
* Reference functions and classes in backticks: `` `function_name()` ``
* Include code examples when relevant
* Keep documentation up to date with code changes
* Use clear, concise language
* Include examples for complex features

## Project Structure

```
git_proj_manger_mcp/
├── src/                        # Source code
│   ├── __init__.py
│   ├── __main__.py            # MCP server entry point
│   ├── cli.py                 # Command-line interface
│   ├── env.py                 # Environment configuration
│   ├── domain/                 # Domain layer
│   │   ├── types.py           # Domain types
│   │   ├── errors.py          # Domain errors
│   │   ├── mcp_types.py       # MCP protocol types
│   │   └── resource_types.py  # Resource type definitions
│   ├── infrastructure/        # Infrastructure layer
│   │   ├── github/            # GitHub API integration
│   │   ├── tools/             # MCP tools layer
│   │   ├── mcp/               # MCP protocol implementation
│   │   ├── cache/             # Caching layer
│   │   ├── events/            # Event system
│   │   └── logger/            # Logging infrastructure
│   └── services/              # Service layer
│       └── project_management_service.py
├── docs/                      # Documentation
├── tests/                      # Test files (if any)
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration
├── README.md                   # Project overview
├── ARCHITECTURE.md             # Architecture documentation
├── CONTRIBUTING.md             # Contribution guidelines
└── LICENSE                     # MIT license
```

## Testing

### Writing Tests

* Write tests for all new features and bug fixes
* Use [pytest](https://docs.pytest.org/) for testing
* Follow the existing testing patterns and conventions
* Include both positive and negative test cases
* Mock external dependencies (GitHub API, cache, etc.)
* Use descriptive test names

Example:

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.domain.types import CreateIssue, Issue

@pytest.mark.asyncio
async def test_create_issue_success():
    """Test successful issue creation."""
    service = ProjectManagementService(...)
    create_data = CreateIssue(
        title="Test Issue",
        description="Test description"
    )
    
    with patch('src.infrastructure.github.repositories.github_issue_repository.GitHubIssueRepository.create') as mock_create:
        mock_create.return_value = Issue(...)
        result = await service.create_issue(create_data)
        
        assert result.title == "Test Issue"
        mock_create.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_issue_repository.py

# Run tests with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_create"
```

### Test Coverage

* Aim for at least 80% code coverage
* Focus on testing business logic and error handling
* Mock external dependencies to avoid API calls in tests
* Test edge cases and error conditions

## Architecture Guidelines

### Clean Architecture

This project follows Clean Architecture principles:

* **Domain Layer**: Core business logic, no external dependencies
* **Infrastructure Layer**: External integrations (GitHub API, MCP)
* **Service Layer**: Business logic coordination
* **Tools Layer**: MCP tool definitions and handlers

When adding new features:

1. Define domain types in `src/domain/`
2. Implement repositories in `src/infrastructure/github/repositories/`
3. Add service methods in `src/services/project_management_service.py`
4. Create tool handlers in `src/infrastructure/tools/tool_handlers.py`
5. Register tools in `src/infrastructure/tools/tool_registry.py`

### Error Handling

* Use domain error types from `src/domain/errors.py`
* Map GitHub API errors to domain errors
* Provide meaningful error messages
* Log errors appropriately

### Async Patterns

* Always use async/await for I/O operations
* Use `asyncio.gather()` for concurrent operations when appropriate
* Handle exceptions in async functions properly

## Additional Notes

### Issue and Pull Request Labels

* `bug`: Something isn't working
* `enhancement`: New feature or request
* `documentation`: Improvements or additions to documentation
* `good first issue`: Good for newcomers
* `help wanted`: Extra attention is needed
* `question`: Further information is requested
* `refactor`: Code refactoring
* `test`: Test-related changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows the styleguide
- [ ] All tests pass
- [ ] Code is formatted with Black
- [ ] No linting errors (Ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

### Getting Help

If you need help:

1. Check the [README](README.md) and [ARCHITECTURE](ARCHITECTURE.md) docs
2. Search existing issues
3. Ask questions in a new issue with the `question` label
4. Reach out to maintainers

## Recognition

Contributors who make significant and valuable contributions will be granted commit access to the project. All contributors will be recognized in the project documentation.

Thank you for contributing! 🎉
