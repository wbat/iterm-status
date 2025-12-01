"""Core plugin for path formatting, job indicator, and clock."""

import datetime
from typing import Any, Dict, List

from ..iterm.session_vars import SessionContext
from ..util.strings import find_repo_root, shorten_path
from .base import BasePlugin


class CorePlugin(BasePlugin):
    """Core plugin providing path, job, and clock information."""

    def get_fields(self) -> List[str]:
        return ["path", "path_short", "path_basename", "repo_root", "job", "clock"]

    def get_dependencies(self) -> List[str]:
        return []  # No external dependencies

    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update core plugin data.

        This plugin doesn't need background updates since it only
        uses session variables that are already available.
        """
        path = context.path or ""
        job = context.job_name or context.command_line or ""

        # Find repo root if path exists
        repo_root = None
        if path:
            repo_root = find_repo_root(path)

        # Format path variants
        path_short = shorten_path(path, max_length=40, style="collapse")
        path_basename = shorten_path(path, max_length=40, style="basename")

        # Get current time
        now = datetime.datetime.now()
        clock = now.strftime("%H:%M")

        return {
            "path": path,
            "path_short": path_short,
            "path_basename": path_basename,
            "repo_root": repo_root or "",
            "job": job[:50] if job else "",  # Limit job name length
            "clock": clock,
        }

    def get_cached(self, context: SessionContext) -> Dict[str, Any]:
        """Get cached core data, or compute on-the-fly if not cached.

        Since core plugin data is cheap to compute, we can compute
        it synchronously if not cached.
        """
        # Try cache first
        cached = super().get_cached(context)
        if cached and any(cached.values()):
            return cached

        # Compute synchronously (it's fast)
        path = context.path or ""
        job = context.job_name or context.command_line or ""

        repo_root = None
        if path:
            repo_root = find_repo_root(path)

        path_short = shorten_path(path, max_length=40, style="collapse")
        path_basename = shorten_path(path, max_length=40, style="basename")

        now = datetime.datetime.now()
        clock = now.strftime("%H:%M")

        data = {
            "path": path,
            "path_short": path_short,
            "path_basename": path_basename,
            "repo_root": repo_root or "",
            "job": job[:50] if job else "",
            "clock": clock,
        }

        # Cache it
        self._set_cached(context, data)

        return data
