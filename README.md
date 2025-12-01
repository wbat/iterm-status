# WBAT iTerm2 Status Bar

[![CI](https://github.com/wbat/iterm-status/actions/workflows/ci.yml/badge.svg)](https://github.com/wbat/iterm-status/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A customizable status bar component for iTerm2 with a plugin system. Displays git, AWS, GCP, Kubernetes, and more - all without slowing down your shell prompt.

## Features

- **Pro Mode**: Python daemon with timer-based updates (never blocks the prompt)
- **Lite Mode**: Shell-only integration for minimal setup
- **Plugin System**: Built-in plugins for Git, AWS, GCP, Kubernetes, and custom commands
- **View Cycling**: Rotate through multiple status bar views automatically
- **Context-Aware**: Automatically shows relevant information based on your current directory and commands
- **Fast**: All expensive operations run in the background with TTL caching

## Quick Start

### Pro Mode (Recommended)

1. **Install dependencies**:
   ```bash
   pip3 install iterm2
   ```

2. **Run installation script**:
   ```bash
   ./scripts/install.sh
   ```

3. **Enable in iTerm2**:
   - Open iTerm2 → Scripts → AutoLaunch
   - Enable `wbat_statusbar.py`
   - Go to Profiles → Session → Configure Status Bar
   - Add "WBAT Status" component

### Lite Mode (Shell-Only)

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
source /path/to/iterm-status/shell/iterm2_user_vars.zsh  # for zsh
# or
source /path/to/iterm-status/shell/iterm2_user_vars.bash  # for bash
```

Then add an interpolated string to your status bar:
- Go to Profiles → Session → Configure Status Bar
- Add an interpolated string component
- Use: `\(user.awsProfile) \(user.gcpProject)`

## Documentation

- [Quickstart Guide](docs/quickstart.md) - Detailed setup instructions
- [Configuration](docs/configuration.md) - Config file reference
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Plugin Development](docs/plugin-dev.md) - Creating custom plugins
- [Security](docs/security.md) - Security considerations

## Built-in Plugins

- **Core**: Path, job name, clock
- **Git**: Branch, status, ahead/behind, changes
- **AWS**: Profile, region, account, role (env-only or identity mode)
- **GCP**: Project, account (env-only or identity mode)
- **Kubernetes**: Context, namespace
- **Command**: Execute custom commands (with safety checks)

## Requirements

- iTerm2 3.0+
- Python 3.9+
- iTerm2 Python API (installed via iTerm2 or `pip3 install iterm2`)

## Development

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd iterm-status
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks** (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Code Quality

This project uses:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting and import sorting
- **Pytest** for testing

**Before committing**, run:
```bash
# Format code
black src/ tests/

# Check and fix linting issues
ruff check --fix src/ tests/

# Run tests
pytest tests/
```

Or use pre-commit hooks (installed above) to automatically format and lint on commit.

### Project Structure

```
src/wbat_statusbar/
├── core/          # Core functionality (config, cache, scheduler, render)
├── iterm/         # iTerm2 integration (components, session vars)
├── plugins/       # Plugin implementations
├── util/          # Utility functions
└── main.py        # Daemon entry point

tests/             # Test suite
scripts/           # Build and installation scripts
shell/             # Shell integration snippets
docs/              # Documentation
```

## License

MIT
