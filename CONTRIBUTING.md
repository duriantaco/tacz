# Contributing to Tacz

Thank you for your interest in contributing to Tacz! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment for all contributors.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports:
- Check the [issue tracker](https://github.com/duriantaco/tacz/issues)
- Make sure you're using the latest version
- Try to reproduce the issue

When reporting bugs, include:
- Your OS and shell (e.g., "Windows 11, PowerShell 7")
- Tacz version (`tacz --version`)
- LLM provider and model
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs

### Suggesting Enhancements

We welcome feature suggestions! Please:
- Check if it's already suggested in issues
- Explain the use case clearly
- Describe the proposed solution
- Consider alternative solutions

### Your First Code Contribution

Good first issues are labeled `good first issue` or `help wanted`.

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- One of: Ollama, llama.cpp

### Environment Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/tacz.git
cd tacz

# 2. Create a venv
python -m venv tacz-dev
source tacz-dev/bin/activate  # On Windows: tacz-dev\Scripts\activate

# 3. Install dev dependencies
pip install -e ".[dev]"
```

### Project Structure

```
tacz/
├── src/tacz/              # Main source code
│   ├── config/           # Configuration handling
│   ├── llms/            # LLM provider implementations
│   │   └── providers/   # Provider-specific code
│   ├── utils/           # Utility functions
│   └── main.py          # Entry point
├── tests/               # Test files
├── docs/                # Documentation
└── pyproject.toml       # Project configuration
```

### Testing

Write tests for new functionality:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_providers.py

# Run with coverage
pytest --cov=tacz tests/
```

## Adding New Features

### New LLM Providers

To add a new provider:

1. Create `src/tacz/llms/providers/your_provider.py`
2. Implement required methods:
   ```python
   class YourProvider:
       def get_options(self, prompt: str, context: str) -> Optional[CommandsResponse]:
           # Implementation
           pass
   
       def is_available(self) -> bool:
           # Check if provider is accessible
           pass
   
       def get_provider_info(self) -> dict:
           # Return provider metadata
           pass
   ```
3. Update `provider_factory.py`
4. Add to constants and setup wizard
5. Add tests

### New Command Categories

To add a new command category:

1. Update `COMMAND_CATEGORIES` in `constants.py`
2. Add category-specific prompts in `templates.py`
3. Update the nano agent's categorization
4. Add tests for the new category

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clear, concise commit messages
   - Include tests for new functionality
   - Update documentation as needed

3. **Before submitting**:
   ```bash
   # Run all checks
   make pre-commit  # or ./scripts/pre-commit.sh
   
   # Make sure tests pass
   pytest
   ```

4. **Create Pull Request**:
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what changes were made and why
   - Include testing instructions

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Added/updated tests
- [ ] All tests pass
- [ ] Tested on [OS/versions]

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release notes
4. Tag the release
5. Publish to PyPI (maintainers only)

## Getting Help

If you need help contributing:

- Open an issue for clarification
- Email me at `aaronoh2015@gmail.com`

## Recognition

Contributors will be:
- Listed in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file
- Mentioned in release notes
- Given credit in the project documentation

Thank you for contributing to Tacz! 🚀