"""Render engine with template resolution, view cycling, and context override detection."""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .logging import setup_logging

logger = setup_logging()


class ViewCycler:
    """Manages view cycling with round-robin and context override support."""
    
    def __init__(
        self,
        views: Dict[str, Dict[str, Any]],
        enabled: bool = True,
        interval_seconds: float = 8.0,
        mode: str = "round_robin",
        start_view: str = "default"
    ):
        self.views = views
        self.enabled = enabled
        self.interval_seconds = interval_seconds
        self.mode = mode
        self.current_view = start_view
        self.last_cycle_time = time.time()
        self.pinned_view: Optional[str] = None
        self.pinned_until: float = 0
        self.context_overrides: Dict[str, Tuple[str, float]] = {}  # pattern -> (view, until)
    
    def get_current_view(self) -> str:
        """Get the current view name, considering cycling and overrides.
        
        Returns:
            View name to use
        """
        # Check for pinned view first
        if self.pinned_view and time.time() < self.pinned_until:
            return self.pinned_view
        
        # Check context overrides
        for pattern, (view, until) in self.context_overrides.items():
            if time.time() < until:
                return view
        
        # Clear expired pins/overrides
        if self.pinned_view and time.time() >= self.pinned_until:
            self.pinned_view = None
        
        expired_patterns = [
            pattern for pattern, (_, until) in self.context_overrides.items()
            if time.time() >= until
        ]
        for pattern in expired_patterns:
            del self.context_overrides[pattern]
        
        # Handle cycling
        if not self.enabled:
            return self.current_view
        
        # Check if it's time to cycle
        if time.time() - self.last_cycle_time >= self.interval_seconds:
            self._cycle_to_next()
            self.last_cycle_time = time.time()
        
        return self.current_view
    
    def _cycle_to_next(self) -> None:
        """Cycle to the next view in round-robin order."""
        if self.mode != "round_robin":
            return
        
        view_names = list(self.views.keys())
        if not view_names:
            return
        
        try:
            current_index = view_names.index(self.current_view)
            next_index = (current_index + 1) % len(view_names)
            self.current_view = view_names[next_index]
        except ValueError:
            # Current view not in list, use first view
            self.current_view = view_names[0]
    
    def pin_view(self, view_name: str, duration_seconds: float = 15.0) -> None:
        """Temporarily pin a view.
        
        Args:
            view_name: View to pin
            duration_seconds: How long to pin (default 15 seconds)
        """
        self.pinned_view = view_name
        self.pinned_until = time.time() + duration_seconds
        logger.debug(f"Pinned view '{view_name}' for {duration_seconds}s")
    
    def add_context_override(
        self,
        pattern: str,
        view_name: str,
        duration_seconds: float = 15.0
    ) -> None:
        """Add a context override that pins a view when pattern matches.
        
        Args:
            pattern: Regex pattern to match against command/job
            view_name: View to show when pattern matches
            duration_seconds: How long to show the view
        """
        self.context_overrides[pattern] = (view_name, time.time() + duration_seconds)
        logger.debug(f"Added context override: {pattern} -> {view_name} for {duration_seconds}s")
    
    def check_context_override(self, command: str, job: str) -> Optional[str]:
        """Check if command/job matches any context override pattern.
        
        Args:
            command: Last command executed
            job: Current job name
            
        Returns:
            View name to use if override matches, None otherwise
        """
        text_to_check = f"{command} {job}".lower()
        
        for pattern, (view, until) in self.context_overrides.items():
            if time.time() >= until:
                continue
            
            try:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    return view
            except re.error:
                logger.warning(f"Invalid regex pattern in context override: {pattern}")
        
        return None


class Renderer:
    """Template renderer that resolves field references to plugin outputs."""
    
    def __init__(
        self,
        views: Dict[str, Dict[str, Any]],
        view_cycler: ViewCycler,
        render_timeout_ms: int = 50
    ):
        self.views = views
        self.view_cycler = view_cycler
        self.render_timeout_ms = render_timeout_ms
        self.field_pattern = re.compile(r"\{([^}]+)\}")
    
    def render(
        self,
        view_name: Optional[str] = None,
        plugin_data: Optional[Dict[str, Dict[str, Any]]] = None,
        context: Optional[Dict[str, str]] = None
    ) -> str:
        """Render a view template with plugin data.
        
        Args:
            view_name: Specific view to render, or None to use cycler
            plugin_data: Dictionary of plugin_name -> field_name -> value
            context: Context data (command, job) for override detection
            
        Returns:
            Rendered string
        """
        if plugin_data is None:
            plugin_data = {}
        
        # Get view name
        if view_name is None:
            # Check for context override
            if context:
                override_view = self.view_cycler.check_context_override(
                    context.get("command", ""),
                    context.get("job", "")
                )
                if override_view:
                    view_name = override_view
                else:
                    view_name = self.view_cycler.get_current_view()
            else:
                view_name = self.view_cycler.get_current_view()
        
        # Get template
        view_config = self.views.get(view_name)
        if not view_config:
            logger.warning(f"View '{view_name}' not found, using default")
            view_config = self.views.get("default", {})
        
        template = view_config.get("template", "")
        if not template:
            return ""
        
        # Render template
        try:
            return self._render_template(template, plugin_data)
        except Exception as e:
            logger.error(f"Error rendering view '{view_name}': {e}", exc_info=True)
            return f"[render error: {e}]"
    
    def _render_template(
        self,
        template: str,
        plugin_data: Dict[str, Dict[str, Any]]
    ) -> str:
        """Render a template string by replacing field references.
        
        Field references are in the format: {plugin.field} or {plugin.field.subfield}
        
        Args:
            template: Template string with {field} references
            plugin_data: Dictionary of plugin_name -> field_name -> value
            
        Returns:
            Rendered string
        """
        def replace_field(match: re.Match) -> str:
            field_ref = match.group(1)
            parts = field_ref.split(".", 1)
            
            if len(parts) == 1:
                # Simple field reference like {path}
                # Try to find in any plugin
                for plugin_name, fields in plugin_data.items():
                    if field_ref in fields:
                        value = fields[field_ref]
                        return self._format_value(value)
                return ""
            
            plugin_name, field_path = parts[0], parts[1]
            
            # Get plugin data
            plugin_fields = plugin_data.get(plugin_name, {})
            
            # Handle nested field paths like git.summary or aws.short
            value = self._get_nested_value(plugin_fields, field_path)
            return self._format_value(value)
        
        result = self.field_pattern.sub(replace_field, template)
        
        # Clean up multiple spaces
        result = re.sub(r"  +", "  ", result)
        result = result.strip()
        
        return result
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., "git.branch" or "summary")
            
        Returns:
            Value or empty string if not found
        """
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return ""
            else:
                return ""
        
        return current if current is not None else ""
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display.
        
        Args:
            value: Value to format
            
        Returns:
            Formatted string
        """
        if value is None:
            return ""
        
        if isinstance(value, (int, float)):
            return str(value)
        
        if isinstance(value, bool):
            return "✓" if value else ""
        
        if isinstance(value, str):
            return value
        
        if isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value)
        
        if isinstance(value, dict):
            # For dicts, try to find a 'display' or 'text' key, or just stringify
            return value.get("display", value.get("text", str(value)))
        
        return str(value)
    
    def extract_fields(self, template: str) -> List[str]:
        """Extract all field references from a template.
        
        Args:
            template: Template string
            
        Returns:
            List of field references (e.g., ["path", "git.branch", "aws.short"])
        """
        fields = []
        for match in self.field_pattern.finditer(template):
            fields.append(match.group(1))
        return fields
