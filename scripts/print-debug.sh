#!/usr/bin/env bash
# Debug script to dump configuration and status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$HOME/.config/wbat-iterm-status/config.toml"
AUTOLAUNCH_DIR="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
SCRIPT_FILE="$AUTOLAUNCH_DIR/wbat_statusbar.py"

echo "WBAT iTerm2 Status Bar - Debug Information"
echo "=========================================="
echo ""

# Python version
echo "Python Version:"
python3 --version
echo ""

# iTerm2 Python API
echo "iTerm2 Python API:"
if python3 -c "import iterm2; print(iterm2.__version__)" 2>/dev/null; then
    echo "✓ Installed"
else
    echo "✗ Not installed"
fi
echo ""

# Script installation
echo "Script Installation:"
if [ -f "$SCRIPT_FILE" ]; then
    echo "✓ Found: $SCRIPT_FILE"
    ls -lh "$SCRIPT_FILE"
else
    echo "✗ Not found: $SCRIPT_FILE"
fi
echo ""

# Configuration
echo "Configuration:"
if [ -f "$CONFIG_FILE" ]; then
    echo "✓ Found: $CONFIG_FILE"
    echo ""
    echo "Config contents:"
    cat "$CONFIG_FILE"
else
    echo "✗ Not found: $CONFIG_FILE"
    echo "  (Will be created on first run)"
fi
echo ""

# Dependencies
echo "Dependencies:"
for cmd in git aws gcloud kubectl; do
    if command -v "$cmd" &> /dev/null; then
        version=$($cmd --version 2>&1 | head -n1)
        echo "✓ $cmd: $version"
    else
        echo "✗ $cmd: not found"
    fi
done
echo ""

# Environment variables
echo "Environment Variables:"
for var in AWS_PROFILE AWS_REGION CLOUDSDK_CORE_PROJECT; do
    if [ -n "${!var}" ]; then
        echo "  $var=${!var}"
    fi
done
echo ""

# Log file
LOG_FILE="$HOME/.config/wbat-iterm-status/statusbar.log"
if [ -f "$LOG_FILE" ]; then
    echo "Recent log entries (last 20 lines):"
    tail -n 20 "$LOG_FILE"
    echo ""
fi

echo "Debug information complete."
