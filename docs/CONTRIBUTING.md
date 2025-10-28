# Contributing to Parallel AI Test Project

Thank you for your interest in contributing to the Parallel AI Test Project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory comments
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Familiarity with parallel processing concepts
- Basic understanding of AI orchestration (helpful but not required)

### Finding Issues to Work On

1. Check the [Issues](https://github.com/yourusername/parallel_ai_test_project/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to express your interest
4. Wait for maintainer approval before starting work

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/parallel_ai_test_project.git
cd parallel_ai_test_project

# Add upstream remote
git remote add upstream https://github.com/original/parallel_ai_test_project.git
```

### 2. Create Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Create a Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a new branch for your feature/fix
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

## Project Structure

```
parallel_ai_test_project/
├── orchestrator/          # Core system code
│   ├── __init__.py       # Public API
│   ├── main.py           # Main orchestrator
│   ├── ai_task_decomposer.py  # Task decomposition
│   ├── worker.py         # Worker implementation
│   ├── monitoring.py     # Monitoring utilities
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging system
│   ├── exceptions.py     # Custom exceptions
│   ├── utils.py          # Utility functions
│   └── validators.py     # Validation functions
│
├── examples/             # Usage examples
├── data/samples/         # Sample data files
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── tests/                # Test suite
└── workspace/            # Runtime workspace (gitignored)
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- Line length: 100 characters (not 79)
- Use 4 spaces for indentation (not tabs)
- Use double quotes for strings (unless single quotes avoid escaping)

### Type Hints

All new code must include type hints:

```python
def process_task(task: str, timeout: int = 120) -> Dict[str, Any]:
    """
    Process a task with specified timeout.

    Args:
        task: Task description
        timeout: Timeout in seconds

    Returns:
        Dictionary containing task results
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed, explaining the function's behavior,
    algorithm, or any important details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
        RuntimeError: When operation fails

    Examples:
        >>> complex_function("test", 5)
        True
    """
    pass
```

### Code Organization

- One class per file (exceptions allowed for small utility classes)
- Group imports: standard library, third-party, local
- Use absolute imports, not relative
- Keep functions focused and single-purpose

### Example

```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional, Any

# Third-party imports
import yaml
import psutil

# Local imports
from orchestrator.config import Config
from orchestrator.exceptions import ConfigurationError


class MyClass:
    """Class description."""

    def __init__(self, config: Config):
        """Initialize MyClass."""
        self.config = config

    def public_method(self) -> str:
        """Public method accessible to users."""
        return self._private_method()

    def _private_method(self) -> str:
        """Private method for internal use only."""
        return "result"
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=orchestrator

# Run specific test file
python -m pytest tests/test_orchestrator.py

# Run specific test
python -m pytest tests/test_orchestrator.py::TestClass::test_method
```

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert

```python
import pytest
from orchestrator import Orchestrator


class TestOrchestrator:
    """Test suite for Orchestrator class."""

    def test_execute_simple_task(self):
        """Test executing a simple single task."""
        # Arrange
        orch = Orchestrator(max_workers=1)
        task = "Create a simple function"

        # Act
        result = orch.execute(task)

        # Assert
        assert result['status'] == 'success'
        assert result['total_tasks'] == 1
        assert result['completed_tasks'] == 1

    def test_execute_with_invalid_task(self):
        """Test that invalid tasks raise appropriate errors."""
        # Arrange
        orch = Orchestrator()

        # Act & Assert
        with pytest.raises(ValueError):
            orch.execute("")
```

### Test Coverage Requirements

- Minimum 80% overall coverage
- 90% coverage for core modules (orchestrator, worker, config)
- 100% coverage for critical paths (error handling, security)

## Submitting Changes

### 1. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add feature: description of feature"
```

### Commit Message Guidelines

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat: Add support for Docker execution mode
fix: Resolve worker timeout issue in subprocess mode
docs: Update API reference for Orchestrator class
test: Add integration tests for monitoring module
```

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:
   - **Title**: Clear, concise description
   - **Description**: What changes were made and why
   - **Related Issues**: Link to relevant issues
   - **Testing**: How the changes were tested
   - **Screenshots**: If applicable

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts
- [ ] PR description is complete

## Documentation

### Updating Documentation

- Update docstrings when changing function signatures
- Update `docs/api_reference.md` for API changes
- Update `docs/user_guide.md` for user-facing changes
- Add examples for new features
- Update README.md if needed

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams where helpful (use Mermaid or ASCII art)
- Keep documentation in sync with code

### Example Documentation

```markdown
## Using Custom Configuration

You can customize the orchestrator behavior using a configuration file:

```python
from orchestrator.config import Config
from orchestrator import Orchestrator

# Load configuration from YAML
config = Config.from_yaml('my_config.yaml')

# Create orchestrator with custom config
orch = Orchestrator(config=config)
```

The configuration file should follow this format:

```yaml
orchestrator:
  max_workers: 5
  timeout: 300
```
```

## Issue Reporting

### Before Creating an Issue

1. Search existing issues to avoid duplicates
2. Check documentation and FAQs
3. Try to reproduce the issue with minimal code
4. Gather relevant information (OS, Python version, logs)

### Bug Reports

Include:
- **Description**: Clear description of the bug
- **Steps to Reproduce**: Minimal steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, package versions
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable

### Feature Requests

Include:
- **Problem**: What problem does this solve?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other solutions considered
- **Use Cases**: Real-world usage scenarios

## Development Workflow

### Typical Workflow

1. **Plan**: Discuss feature/fix in issue
2. **Branch**: Create feature branch
3. **Develop**: Write code with tests
4. **Test**: Run full test suite
5. **Document**: Update relevant documentation
6. **Commit**: Make clear, focused commits
7. **Push**: Push to your fork
8. **PR**: Create pull request
9. **Review**: Address review feedback
10. **Merge**: Maintainer merges PR

### Code Review Process

- All PRs require at least one review
- Address all review comments
- Be respectful and constructive
- Focus on code quality and correctness
- Explain rationale for changes

## Release Process

Maintainers handle releases using semantic versioning:

- **Major** (X.0.0): Breaking changes
- **Minor** (x.Y.0): New features, backwards compatible
- **Patch** (x.y.Z): Bug fixes, backwards compatible

## Getting Help

- **Documentation**: Check [docs/](docs/)
- **Examples**: See [examples/](examples/)
- **Issues**: Search or create new issue
- **Discussions**: Use GitHub Discussions for questions

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

## Quick Reference

### Common Commands

```bash
# Setup
git clone https://github.com/YOUR_USERNAME/parallel_ai_test_project.git
cd parallel_ai_test_project
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Development
git checkout -b feature/my-feature
# ... make changes ...
python -m pytest
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature

# Staying Updated
git checkout main
git pull upstream main
git push origin main
```

### Need Help?

Don't hesitate to ask questions! We're here to help new contributors.

Thank you for contributing to the Parallel AI Test Project! 🚀
