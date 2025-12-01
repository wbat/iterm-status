# Security Guide

Security considerations for WBAT iTerm2 Status Bar.

## Overview

WBAT iTerm2 Status Bar executes commands and reads system information. This guide covers security best practices.

## Command Execution

### Generic Command Plugin

The `cmd` plugin allows executing arbitrary commands. **Use with caution**.

**Safety Features**:
- Command validation (blocks dangerous patterns)
- Timeout enforcement
- Output size limits
- Error isolation

**Dangerous Patterns Blocked**:
- `rm -rf`
- `rm -r`
- `dd if=`
- `mkfs`
- `format`
- Shell piping (`| sh`, `| bash`)

**Recommendations**:
1. Only use commands you trust
2. Use absolute paths when possible
3. Set short timeouts
4. Limit output size
5. Review command output

### Plugin Commands

Built-in plugins execute specific commands:
- Git: `git status`, `git rev-parse`, etc.
- AWS: `aws sts get-caller-identity`
- GCP: `gcloud config get-value`
- Kubernetes: `kubectl config`

These are considered safe, but ensure:
- CLI tools are from trusted sources
- Credentials are properly managed
- Output is sanitized

## File System Access

### Configuration Files

The daemon reads:
- `~/.config/wbat-iterm-status/config.toml`
- `~/Library/Application Support/wbat-iterm-status/config.toml`

**Recommendations**:
- Use restrictive file permissions: `chmod 600 config.toml`
- Don't store secrets in config files
- Review config before using

### Log Files

Logs are written to:
- `~/.config/wbat-iterm-status/statusbar.log`

**Recommendations**:
- Review logs periodically
- Rotate logs (automatic, 10MB max)
- Don't log sensitive information

## Network Access

### AWS/GCP Identity Mode

When using identity mode, plugins query cloud APIs:
- AWS: `aws sts get-caller-identity`
- GCP: `gcloud config get-value account`

**Recommendations**:
- Use environment variables when possible (env_only mode)
- Ensure credentials are properly secured
- Use IAM roles with minimal permissions
- Review cloud provider security best practices

## Environment Variables

Shell integration reads environment variables:
- `AWS_PROFILE`
- `AWS_REGION`
- `CLOUDSDK_CORE_PROJECT`

**Recommendations**:
- Don't export sensitive values
- Use profile/region names only
- Review shell integration scripts before sourcing

## iTerm2 Integration

### Session Variables

The daemon reads iTerm2 session variables:
- `session.path`
- `session.commandLine`
- `user.*` variables

**Recommendations**:
- Be aware of what data is exposed
- Don't set sensitive data in `user.*` variables
- Review shell integration scripts

### Python API

The daemon uses iTerm2's Python API, which has access to:
- Terminal sessions
- Window/tab management
- Variable reading/writing

**Recommendations**:
- Only install scripts from trusted sources
- Review script code before installing
- Use iTerm2's script security features

## Installation Security

### Installation Script

The install script:
- Copies files to iTerm2 AutoLaunch
- Creates configuration directories
- Checks dependencies

**Recommendations**:
- Review install script before running
- Verify file integrity
- Use official releases

### Zipapp Bundle

The zipapp is a single-file Python application.

**Recommendations**:
- Verify bundle integrity
- Review source code
- Use official releases

## Best Practices

1. **Review Configuration**: Check config files before use
2. **Limit Command Plugin**: Use sparingly, only trusted commands
3. **Secure Credentials**: Use proper credential management
4. **Update Regularly**: Keep dependencies updated
5. **Monitor Logs**: Review logs for suspicious activity
6. **Principle of Least Privilege**: Use minimal permissions
7. **Audit Plugins**: Review plugin code before use

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email security details to the maintainers
3. Include:
   - Description of the issue
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Checklist

- [ ] Configuration files have restrictive permissions
- [ ] No secrets stored in config files
- [ ] Command plugin used only for trusted commands
- [ ] Cloud credentials properly secured
- [ ] Shell integration scripts reviewed
- [ ] Logs reviewed periodically
- [ ] Dependencies kept up to date
- [ ] Official releases used

## See Also

- [iTerm2 Security](https://iterm2.com/documentation-security.html)
- [Python Security](https://python.readthedocs.io/en/latest/library/security.html)
- [Configuration Guide](configuration.md)
