"""Git plugin with async git commands, fast mode, and background updates."""

from typing import Any, Dict, List

from ..iterm.session_vars import SessionContext
from ..util.subprocess import run_command_safe
from ..util.strings import find_repo_root
from .base import BasePlugin


class GitPlugin(BasePlugin):
    """Git plugin providing branch, status, and change information."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = self.config.get("mode", "fast")
        self.max_repo_scan_ms = self.config.get("max_repo_scan_ms", 50)

    def get_fields(self) -> List[str]:
        return [
            "branch",
            "summary",
            "ahead_behind",
            "changes",
            "dirty",
            "staged",
            "unstaged",
        ]

    def get_dependencies(self) -> List[str]:
        return ["git"]

    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update git plugin data."""
        path = context.path or ""
        if not path:
            return self._get_default_values()

        # Find repo root
        repo_root = find_repo_root(path)
        if not repo_root:
            return self._get_default_values()

        # Get branch name
        branch = await run_command_safe(
            "git rev-parse --abbrev-ref HEAD", cwd=repo_root, timeout=1.0, default=""
        )

        if not branch:
            return self._get_default_values()

        # Get status (fast mode: just check if dirty)
        if self.mode == "fast":
            # Quick status check
            status_output = await run_command_safe(
                "git status --porcelain", cwd=repo_root, timeout=0.5, default=""
            )

            dirty = bool(status_output)
            staged_lines = [
                line
                for line in status_output.split("\n")
                if line.startswith(("M ", "A ", "D ", "R "))
            ]
            unstaged_lines = [
                line
                for line in status_output.split("\n")
                if line.startswith((" M", " A", " D", " R", "??"))
            ]
            staged_count = len(staged_lines)
            unstaged_count = len(unstaged_lines)
        else:
            # Full status (slower but more detailed)
            status_output = await run_command_safe(
                "git status --short", cwd=repo_root, timeout=2.0, default=""
            )
            dirty = bool(status_output)
            lines = status_output.split("\n")
            staged_count = len([line for line in lines if line and line[0] != " "])
            unstaged_count = len([line for line in lines if line and line[0] == " "])

        # Get ahead/behind (async, can be slow)
        ahead_behind = ""
        try:
            upstream = await run_command_safe(
                "git rev-parse --abbrev-ref --symbolic-full-name @{u}",
                cwd=repo_root,
                timeout=1.0,
                default="",
            )

            if upstream:
                ahead_behind_output = await run_command_safe(
                    f"git rev-list --left-right --count HEAD...{upstream}",
                    cwd=repo_root,
                    timeout=1.0,
                    default="",
                )

                if ahead_behind_output:
                    parts = ahead_behind_output.strip().split()
                    if len(parts) == 2:
                        behind = int(parts[0])
                        ahead = int(parts[1])
                        if ahead > 0 or behind > 0:
                            ahead_behind = f"+{ahead}" if ahead > 0 else ""
                            ahead_behind += f"-{behind}" if behind > 0 else ""
        except Exception:
            pass  # Ignore errors in ahead/behind calculation

        # Build summary
        summary_parts = [branch]
        if ahead_behind:
            summary_parts.append(ahead_behind)
        if dirty:
            summary_parts.append("●")

        summary = " ".join(summary_parts)

        # Build changes string
        changes_parts = []
        if staged_count > 0:
            changes_parts.append(f"+{staged_count}")
        if unstaged_count > 0:
            changes_parts.append(f"~{unstaged_count}")
        changes = " ".join(changes_parts)

        data = {
            "branch": branch,
            "summary": summary,
            "ahead_behind": ahead_behind,
            "changes": changes,
            "dirty": dirty,
            "staged": staged_count,
            "unstaged": unstaged_count,
        }

        self._set_cached(context, data)
        return data
