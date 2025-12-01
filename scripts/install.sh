#!/usr/bin/env bash
# Installation script for WBAT iTerm2 Status Bar

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AUTOLAUNCH_DIR="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
CONFIG_DIR="$HOME/.config/wbat-iterm-status"
CONFIG_FILE="$CONFIG_DIR/config.toml"

echo "WBAT iTerm2 Status Bar - Installation"
echo "===================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "✗ Python 3.9+ is required, found Python $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"

# Check if iTerm2 Python API is available
if ! python3 -c "import iterm2" 2>/dev/null; then
    echo ""
    echo "⚠ iTerm2 Python API not found"
    echo "  Please install it via:"
    echo "    1. Open iTerm2"
    echo "    2. Go to Scripts → Manage → Install Python Runtime"
    echo "    3. Or install via: pip3 install iterm2"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ iTerm2 Python API found"
fi

# Build zipapp if it doesn't exist
if [ ! -f "$REPO_ROOT/dist/wbat_statusbar.py" ]; then
    echo ""
    echo "Building zipapp..."
    python3 "$REPO_ROOT/scripts/build.py"
fi

# Create AutoLaunch directory
echo ""
echo "Installing to iTerm2 AutoLaunch..."
mkdir -p "$AUTOLAUNCH_DIR"

# Copy script
cp "$REPO_ROOT/dist/wbat_statusbar.py" "$AUTOLAUNCH_DIR/wbat_statusbar.py"
chmod +x "$AUTOLAUNCH_DIR/wbat_statusbar.py"
echo "✓ Installed script to: $AUTOLAUNCH_DIR/wbat_statusbar.py"

# Create config directory and default config if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    echo "Creating default configuration..."
    mkdir -p "$CONFIG_DIR"
    # Config will be created on first run if not present
    echo "✓ Config directory created: $CONFIG_DIR"
    echo "  (Default config will be created on first run)"
else
    echo "✓ Using existing config: $CONFIG_FILE"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Open iTerm2"
echo "2. Go to Scripts → AutoLaunch"
echo "3. Enable 'wbat_statusbar.py'"
echo "4. Go to Profiles → Session → Configure Status Bar"
echo "5. Add 'WBAT Status' component to your status bar"
echo ""
echo "For Lite mode (shell-only), add to your ~/.zshrc or ~/.bashrc:"
echo "  source $REPO_ROOT/shell/iterm2_user_vars.zsh  # for zsh"
echo "  source $REPO_ROOT/shell/iterm2_user_vars.bash  # for bash"
echo ""
