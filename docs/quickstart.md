# Quickstart Guide

This guide will help you get WBAT iTerm2 Status Bar up and running.

## Prerequisites

- iTerm2 3.0 or later
- Python 3.9 or later
- iTerm2 Python API enabled

## Step 1: Install iTerm2 Python API

1. Open iTerm2
2. Go to **Scripts → Manage**
3. Click **Install Python Runtime**
4. Or install via command line:
   ```bash
   pip3 install iterm2
   ```

## Step 2: Install WBAT Status Bar

### Option A: Pro Mode (Recommended)

1. Clone or download this repository
2. Run the installation script:
   ```bash
   ./scripts/install.sh
   ```

The script will:
- Check Python version
- Verify iTerm2 Python API
- Build the zipapp bundle
- Copy script to iTerm2 AutoLaunch folder
- Create default configuration

### Option B: Lite Mode (Shell-Only)

1. Add shell integration to your `~/.zshrc` or `~/.bashrc`:
   ```bash
   source /path/to/iterm-status/shell/iterm2_user_vars.zsh
   ```

2. Restart your terminal or run:
   ```bash
   source ~/.zshrc
   ```

## Step 3: Enable in iTerm2

### Pro Mode

1. Open iTerm2
2. Go to **Scripts → AutoLaunch**
3. Find `wbat_statusbar.py` and enable it
4. Go to **Profiles → Session → Configure Status Bar**
5. Click **+** to add a component
6. Select **WBAT Status** from the list
7. Drag it to your desired position

### Lite Mode

1. Go to **Profiles → Session → Configure Status Bar**
2. Click **+** to add a component
3. Select **Interpolated String**
4. Enter your template, e.g.:
   ```
   \(user.awsProfile) \(user.gcpProject) \(user.gitInfo)
   ```

## Step 4: Configure (Optional)

The default configuration will be created at:
- `~/.config/wbat-iterm-status/config.toml`

Edit this file to customize:
- Views and templates
- Plugin settings
- Update intervals
- View cycling

See [Configuration Guide](configuration.md) for details.

## Step 5: Verify Installation

1. Open a new iTerm2 window
2. Navigate to a git repository
3. Check that the status bar shows git information
4. If using AWS/GCP, set environment variables:
   ```bash
   export AWS_PROFILE=my-profile
   export CLOUDSDK_CORE_PROJECT=my-project
   ```

## Troubleshooting

If the status bar doesn't appear:

1. Check that the script is enabled in AutoLaunch
2. Verify the component is added to your status bar
3. Check logs: `~/.config/wbat-iterm-status/statusbar.log`
4. Run debug script: `./scripts/print-debug.sh`

See [Troubleshooting Guide](troubleshooting.md) for more help.
