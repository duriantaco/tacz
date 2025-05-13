# Tacz Tests

This directory contains unit tests for the Tacz application.

## Running Tests

To run all tests:

```bash
# From the project root directory
pytest

# To see verbose output
pytest -v

# To run a specific test file
pytest tests/test_config.py

# To run a specific test
pytest tests/test_config.py::test_get_tacz_dir
```

## Test Coverage

To check test coverage:

```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run tests with coverage
pytest --cov=tacz tests/

# For a detailed HTML report
pytest --cov=tacz --cov-report=html tests/
# Then open htmlcov/index.html in your browser
```

## Test Structure

- `conftest.py` - Shared fixtures and setup
- `test_config.py` - Tests for configuration module
- `test_command_db.py` - Tests for the command database
- `test_ollama_provider.py` - Tests for the Ollama LLM provider
- `test_safety.py` - Tests for safety utilities
- `test_os_detect.py` - Tests for OS detection utilities

## Writing New Tests

When adding new tests:

1. Follow the existing pattern of test organization
2. Keep tests small and focused
3. Use fixtures from conftest.py where appropriate
4. Mock external dependencies
5. Add proper assertions