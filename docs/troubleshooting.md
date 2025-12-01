# Troubleshooting Guide

Common issues and solutions for WBAT iTerm2 Status Bar.

## Status Bar Not Appearing

### Check Script is Enabled

1. Open iTerm2
2. Go to **Scripts → AutoLaunch**
3. Verify `wbat_statusbar.py` is enabled (checkbox checked)

### Check Component is Added

1. Go to **Profiles → Session → Configure Status Bar**
2. Verify "WBAT Status" component is in your status bar
3. If not, add it by clicking **+** and selecting "WBAT Status"

### Check Logs

View the log file for errors:
```bash
tail -f ~/.config/wbat-iterm-status/statusbar.log
```

### Run Debug Script

```bash
./scripts/print-debug.sh
```

This will show:
- Python version
- iTerm2 Python API status
- Script installation status
- Configuration
- Dependencies
- Environment variables
- Recent log entries

## Status Bar Shows "[error: ...]"

### Check Plugin Dependencies

Some plugins require CLI tools:
- Git plugin: requires `git`
- AWS plugin (identity mode): requires `aws`
- GCP plugin (identity mode): requires `gcloud`
- Kubernetes plugin: requires `kubectl`

Verify tools are installed:
```bash
which git aws gcloud kubectl
```

### Check Plugin Configuration

Verify plugins are enabled in config:
```bash
cat ~/.config/wbat-iterm-status/config.toml | grep -A 5 "\[plugins"
```

### Check Logs

Look for specific error messages:
```bash
grep -i error ~/.config/wbat-iterm-status/statusbar.log
```

## Status Bar Updates Slowly

### Increase Update Cadence

Edit config to update less frequently:
```toml
[global]
update_cadence_seconds = 2  # Update every 2 seconds instead of 1
```

### Disable Expensive Plugins

Disable plugins you don't need:
```toml
[plugins.kube]
enabled = false
```

### Use Fast Mode for Git

```toml
[plugins.git]
mode = "fast"
```

## Git Information Not Showing

### Check Git Repository

Verify you're in a git repository:
```bash
git status
```

### Check Git Plugin

Verify git plugin is enabled:
```toml
[plugins.git]
enabled = true
```

### Check Permissions

Ensure you have read access to `.git` directory.

## AWS/GCP Information Not Showing

### Check Environment Variables

For Lite mode, ensure variables are set:
```bash
echo $AWS_PROFILE
echo $CLOUDSDK_CORE_PROJECT
```

### Check Shell Integration

For Pro mode, ensure shell integration is running:
```bash
# Add to ~/.zshrc or ~/.bashrc
source /path/to/iterm-status/shell/iterm2_user_vars.zsh
```

### Check Plugin Mode

For identity mode, ensure CLI tools are configured:
```bash
aws sts get-caller-identity
gcloud config get-value account
```

## View Cycling Not Working

### Check Cycle Settings

Verify cycling is enabled:
```toml
[cycle]
enabled = true
interval_seconds = 8
```

### Check Multiple Views

Ensure you have multiple views defined:
```toml
[views.default]
template = "..."
[views.cloud]
template = "..."
```

## Performance Issues

### Reduce Update Frequency

```toml
[global]
update_cadence_seconds = 5  # Update every 5 seconds
```

### Increase Plugin TTLs

Cache results longer:
```toml
[plugins.aws]
ttl_seconds = 900  # 15 minutes instead of 10
```

### Disable Unused Plugins

Disable plugins you don't use:
```toml
[plugins.kube]
enabled = false
```

## Python Errors

### Check Python Version

Requires Python 3.9+:
```bash
python3 --version
```

### Check iTerm2 Python API

```bash
python3 -c "import iterm2; print(iterm2.__version__)"
```

If not installed:
```bash
pip3 install iterm2
```

### Check Dependencies

```bash
pip3 install iterm2 tomli tomli-w
```

## Still Having Issues?

1. Run the debug script: `./scripts/print-debug.sh`
2. Check logs: `~/.config/wbat-iterm-status/statusbar.log`
3. Check iTerm2 console: **Window → Show Console**
4. Open an issue on GitHub with:
   - Output of debug script
   - Relevant log entries
   - iTerm2 version
   - Python version
