"""String utilities: path shortening, truncation, template helpers."""

import os
import re
from pathlib import Path
from typing import List, Optional


def shorten_path(path: str, max_length: int = 40, style: str = "collapse") -> str:
    """Shorten a file path for display.

    Args:
        path: Full path to shorten
        max_length: Maximum length of result
        style: Shortening style ("collapse", "truncate", "basename")

    Returns:
        Shortened path
    """
    if not path:
        return ""

    if len(path) <= max_length:
        return path

    if style == "basename":
        return os.path.basename(path)

    if style == "truncate":
        return path[: max_length - 3] + "..."

    # Default: collapse style (show beginning and end)
    if style == "collapse":
        # Try to collapse middle segments
        parts = Path(path).parts

        if len(parts) <= 2:
            # Can't collapse much
            return truncate_string(path, max_length)

        # Show first and last parts, collapse middle
        first = parts[0]
        last = parts[-1]

        # Try to fit first + "..." + last
        min_length = len(first) + len(last) + 3
        if min_length > max_length:
            # Just show last part
            return truncate_string(last, max_length)

        # Collapse middle parts
        middle = "..."
        result = f"{first}/{middle}/{last}"

        if len(result) > max_length:
            # Truncate first part if needed
            available = max_length - len(middle) - len(last) - 1
            if available > 0:
                first_truncated = truncate_string(first, available)
                result = f"{first_truncated}/{middle}/{last}"
            else:
                result = truncate_string(last, max_length)

        return result

    return truncate_string(path, max_length)


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s

    if len(suffix) >= max_length:
        return suffix[:max_length]

    return s[: max_length - len(suffix)] + suffix


def find_repo_root(path: str) -> Optional[str]:
    """Find the root of a git repository.

    Args:
        path: Starting path

    Returns:
        Repository root path or None
    """
    current = Path(path).resolve()

    # Check if path itself is a git repo
    if (current / ".git").exists():
        return str(current)

    # Walk up the directory tree
    for parent in current.parents:
        if (parent / ".git").exists():
            return str(parent)

    return None


def extract_template_variables(template: str) -> List[str]:
    """Extract variable names from a template string.

    Args:
        template: Template string with {variable} references

    Returns:
        List of variable names
    """
    pattern = re.compile(r"\{([^}]+)\}")
    return [match.group(1) for match in pattern.finditer(template)]


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "5m 30s", "2h 15m")
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    if minutes < 60:
        if secs > 0:
            return f"{minutes}m {secs}s"
        return f"{minutes}m"

    hours = minutes // 60
    minutes = minutes % 60

    if minutes > 0:
        return f"{hours}h {minutes}m"
    return f"{hours}h"


def format_bytes(bytes_count: int) -> str:
    """Format bytes to human-readable string.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "500 KB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"
