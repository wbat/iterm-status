#!/usr/bin/env bash
# Uninstallation script for WBAT iTerm2 Status Bar

set -e

AUTOLAUNCH_DIR="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
SCRIPT_FILE="$AUTOLAUNCH_DIR/wbat_statusbar.py"
CONFIG_DIR="$HOME/.config/wbat-iterm-status"

echo "WBAT iTerm2 Status Bar - Uninstallation"
echo "========================================"
echo ""

# Remove script
if [ -f "$SCRIPT_FILE" ]; then
    echo "Removing script: $SCRIPT_FILE"
    rm "$SCRIPT_FILE"
    echo "✓ Script removed"
else
    echo "⚠ Script not found: $SCRIPT_FILE"
fi

# Ask about config
if [ -d "$CONFIG_DIR" ]; then
    echo ""
    read -p "Remove configuration directory? ($CONFIG_DIR) [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo "✓ Configuration removed"
    else
        echo "✓ Configuration kept"
    fi
fi

echo ""
echo "Uninstallation complete!"
echo ""
echo "Note: You may need to:"
echo "1. Disable the script in iTerm2: Scripts → AutoLaunch"
echo "2. Remove the component from your status bar: Profiles → Session → Configure Status Bar"
echo "3. Remove shell integration from your ~/.zshrc or ~/.bashrc if added"
echo ""
