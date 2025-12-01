"""Generic command plugin with safety features."""

import shlex
from typing import Any, Dict, List

from ..iterm.session_vars import SessionContext
from ..util.subprocess import run_command_safe
from .base import BasePlugin


class CmdPlugin(BasePlugin):
    """Generic command plugin that executes a configured command."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = self.config.get("command", "")
        self.field_name = self.config.get("field_name", "output")
        self.timeout = self.config.get("timeout", 5.0)
        self.max_output = self.config.get("max_output", 1024)  # Limit to 1KB by default
        self.cwd = self.config.get("cwd", None)
        
        # Safety: validate command is not dangerous
        if self.command:
            self._validate_command()
    
    def _validate_command(self) -> None:
        """Validate that command is safe to run.
        
        Raises:
            ValueError: If command is considered unsafe
        """
        dangerous_patterns = [
            "rm -rf",
            "rm -r",
            "rm -f",
            "dd if=",
            "mkfs",
            "format",
            "> /dev/",
            "| sh",
            "| bash",
        ]
        
        cmd_lower = self.command.lower()
        for pattern in dangerous_patterns:
            if pattern in cmd_lower:
                raise ValueError(f"Command contains potentially dangerous pattern: {pattern}")
    
    def get_fields(self) -> List[str]:
        return [self.field_name]
    
    def get_dependencies(self) -> List[str]:
        # Parse command to get first word
        if not self.command:
            return []
        
        try:
            parts = shlex.split(self.command)
            if parts:
                return [parts[0]]
        except Exception:
            pass
        
        return []
    
    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update command plugin data by executing the configured command."""
        if not self.command:
            return {self.field_name: ""}
        
        # Determine working directory
        cwd = self.cwd
        if not cwd:
            # Use session path if available
            cwd = context.path if context.path else None
        
        try:
            output = await run_command_safe(
                self.command,
                timeout=self.timeout,
                max_output=self.max_output,
                cwd=cwd,
                default=""
            )
            
            # Truncate if needed
            if len(output) > self.max_output:
                output = output[:self.max_output - 3] + "..."
            
            data = {self.field_name: output.strip()}
            self._set_cached(context, data)
            return data
        except Exception as e:
            self.set_error(e)
            return {self.field_name: f"[error: {e}]"}
