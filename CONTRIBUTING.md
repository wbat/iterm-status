# Contributing to WBAT iTerm2 Status Bar

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone <your-fork-url>
   cd iterm-status
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks** (recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Code Style

### Formatting

- **Black**: All code is formatted with Black (line length: 100)
- **Ruff**: Used for linting and import sorting
- Configuration is in `pyproject.toml`

### Before Committing

Run these commands to ensure code quality:

```bash
# Format code
black src/ tests/

# Check and auto-fix linting issues
ruff check --fix src/ tests/

# Run tests
pytest tests/
```

If you've installed pre-commit hooks, these will run automatically on commit.

### Code Guidelines

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and small
- Handle errors gracefully with appropriate logging
- Use async/await for I/O operations

## Testing

- Write tests for new features
- Ensure all tests pass: `pytest tests/`
- Aim for good test coverage
- Test fixtures are in `tests/fixtures/`

## Pull Requests

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Ensure quality checks pass**:
   ```bash
   black src/ tests/
   ruff check src/ tests/
   pytest tests/
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push and create a PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Plugin Development

See [docs/plugin-dev.md](docs/plugin-dev.md) for detailed instructions on creating custom plugins.

## Questions?

Feel free to open an issue for questions or discussions about contributions.

