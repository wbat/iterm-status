# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-XX

### Added
- Pro Mode: Python daemon with timer-based updates
- Lite Mode: Shell-only integration
- Plugin system with built-in plugins:
  - Core plugin (path, job, clock)
  - Git plugin (branch, status, changes)
  - AWS plugin (profile, region, identity)
  - GCP plugin (project, account)
  - Kubernetes plugin (context, namespace)
  - Command plugin (custom commands)
- View cycling with multiple views
- Context-aware status bar
- TTL-based caching system
- Background task scheduler
- Configuration file support (TOML)
- Shell integration snippets (zsh, bash, fish)
- Installation and uninstallation scripts
- Debug script
- Comprehensive documentation
- Unit tests
- CI/CD workflows

### Changed
- Complete rewrite from v1 shell-only approach
- Now uses iTerm2 Python API for native integration

### Security
- Command validation for generic command plugin
- Timeout enforcement for all subprocess calls
- Output size limits
- Error isolation
