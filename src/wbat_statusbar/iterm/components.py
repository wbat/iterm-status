"""StatusBarComponent registration with knobs and click handlers."""

import asyncio
from typing import Any, Callable, Dict, Optional

try:
    import iterm2
except ImportError:
    iterm2 = None  # Optional for testing

from ..core.logging import setup_logging

logger = setup_logging()


class StatusBarComponent:
    """Wrapper for iTerm2 StatusBarComponent with additional features."""
    
    def __init__(
        self,
        component,  # iterm2.StatusBarComponent when available
        render_func: Callable[[], str],
        update_cadence: float = 1.0
    ):
        self.component = component
        self.render_func = render_func
        self.update_cadence = update_cadence
        self._pinned = False
        self._view_index = 0
    
    async def render(self) -> str:
        """Render the status bar text.
        
        Returns:
            Status bar text
        """
        try:
            return self.render_func()
        except Exception as e:
            logger.error(f"Error rendering status bar: {e}", exc_info=True)
            return f"[error: {e}]"
    
    def toggle_pin(self) -> None:
        """Toggle pin state."""
        self._pinned = not self._pinned
        logger.debug(f"Pin toggled: {self._pinned}")
    
    def is_pinned(self) -> bool:
        """Check if component is pinned."""
        return self._pinned


class ComponentRegistry:
    """Registry for managing status bar components."""
    
    def __init__(self, connection):
        self.connection = connection
        self.components: Dict[str, StatusBarComponent] = {}
        self._render_callbacks: Dict[str, Callable[[], str]] = {}
    
    async def register_component(
        self,
        component_id: str,
        short_description: str,
        detailed_description: str,
        render_func: Callable[[], str],
        update_cadence: float = 1.0,
        knobs: Optional[Dict[str, Any]] = None
    ):
        """Register a status bar component.
        
        Args:
            component_id: Unique identifier for the component
            short_description: Short description shown in UI
            detailed_description: Detailed description/tooltip
            render_func: Function that returns the status bar text
            update_cadence: Update interval in seconds
            knobs: Optional dictionary of knob configurations
            
        Returns:
            iTerm2 StatusBarComponent instance
        """
        # Create knobs
        knob_list = []
        
        if knobs is None:
            knobs = {}
        
        # Add cycle toggle knob
        cycle_knob = iterm2.SimpleKnob(
            "Cycle Enabled",
            knobs.get("cycle_enabled", True),
            "Enable view cycling"
        )
        knob_list.append(cycle_knob)
        
        # Add cycle interval knob
        cycle_interval_knob = iterm2.StringKnob(
            "Cycle Interval (seconds)",
            str(knobs.get("cycle_interval", 8)),
            "Interval between view cycles"
        )
        knob_list.append(cycle_interval_knob)
        
        # Create component
        if iterm2 is None:
            raise RuntimeError("iterm2 module not available")
        component = iterm2.StatusBarComponent.create_simple_component(
            component_id,
            short_description,
            detailed_description,
            update_cadence,
            self._create_click_handler(component_id),
            knob_list
        )
        
        # Register component
        await component.async_register(self.connection)
        
        # Store wrapper
        wrapper = StatusBarComponent(component, render_func, update_cadence)
        self.components[component_id] = wrapper
        self._render_callbacks[component_id] = render_func
        
        logger.info(f"Registered component: {component_id}")
        return component
    
    def _create_click_handler(self, component_id: str) -> Callable:
        """Create a click handler for a component.
        
        Args:
            component_id: Component identifier
            
        Returns:
            Click handler function
        """
        async def click_handler(component: iterm2.StatusBarComponent) -> None:
            """Handle click on status bar component."""
            wrapper = self.components.get(component_id)
            if wrapper:
                wrapper.toggle_pin()
                logger.debug(f"Component {component_id} clicked, pin={wrapper.is_pinned()}")
        
        return click_handler
    
    def get_component(self, component_id: str) -> Optional[StatusBarComponent]:
        """Get a component by ID.
        
        Args:
            component_id: Component identifier
            
        Returns:
            StatusBarComponent or None
        """
        return self.components.get(component_id)
    
    async def update_component(self, component_id: str) -> None:
        """Update a component's display.
        
        Args:
            component_id: Component identifier
        """
        wrapper = self.components.get(component_id)
        if wrapper:
            try:
                text = await wrapper.render()
                await wrapper.component.async_set_text(text)
            except Exception as e:
                logger.error(f"Error updating component {component_id}: {e}", exc_info=True)
    
    async def update_all_components(self) -> None:
        """Update all registered components."""
        tasks = [
            self.update_component(component_id)
            for component_id in self.components.keys()
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
