"""Plugin manager for discovery, loading, and lifecycle management."""

from typing import Any, Dict, Optional

from ..core.cache import Cache
from ..core.logging import setup_logging
from ..core.scheduler import Scheduler
from ..iterm.session_vars import SessionContext
from ..plugins.aws import AWSPlugin
from ..plugins.base import BasePlugin
from ..plugins.cmd import CmdPlugin
from ..plugins.core import CorePlugin
from ..plugins.gcp import GCPPlugin
from ..plugins.git import GitPlugin
from ..plugins.kube import KubePlugin

logger = setup_logging()

# Built-in plugin registry
BUILTIN_PLUGINS = {
    "core": CorePlugin,
    "git": GitPlugin,
    "aws": AWSPlugin,
    "gcp": GCPPlugin,
    "kube": KubePlugin,
    "cmd": CmdPlugin,
}


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""
    
    def __init__(self, config: Dict, cache: Cache, scheduler: Scheduler):
        self.config = config
        self.cache = cache
        self.scheduler = scheduler
        self.plugins: Dict[str, BasePlugin] = {}
        self._plugin_configs = config.get("plugins", {})
    
    def load_plugins(self) -> None:
        """Load all enabled plugins from config."""
        for plugin_name, plugin_class in BUILTIN_PLUGINS.items():
            plugin_config = self._plugin_configs.get(plugin_name, {})
            
            # Check if plugin is enabled
            if not plugin_config.get("enabled", True):
                logger.debug(f"Plugin {plugin_name} is disabled, skipping")
                continue
            
            try:
                plugin = plugin_class(
                    name=plugin_name,
                    config=plugin_config,
                    cache=self.cache,
                    scheduler=self.scheduler
                )
                
                # Check dependencies
                if not plugin.check_dependencies():
                    logger.warning(
                        f"Plugin {plugin_name} missing dependencies, "
                        f"but loading anyway (will show empty values)"
                    )
                
                self.plugins[plugin_name] = plugin
                logger.info(f"Loaded plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins.
        
        Returns:
            Dictionary of plugin_name -> plugin
        """
        return self.plugins.copy()
    
    async def register_plugin_tasks(self, context: SessionContext) -> None:
        """Register background update tasks for all plugins.
        
        Args:
            context: Session context
        """
        for plugin_name, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
            
            task_id = f"{plugin_name}:{context.session_id}"
            
            # Create update coroutine
            async def update_plugin(plugin=plugin, ctx=context):
                try:
                    data = await plugin.update(ctx)
                    logger.debug(f"Plugin {plugin.name} updated: {len(data)} fields")
                except Exception as e:
                    plugin.set_error(e)
                    logger.error(f"Plugin {plugin.name} update failed: {e}", exc_info=True)
            
            # Register with scheduler
            await self.scheduler.register(
                task_id=task_id,
                coro=update_plugin,
                ttl_seconds=plugin.ttl_seconds
            )
            
            # Trigger initial update
            await self.scheduler.trigger(task_id)
    
    def get_plugin_data(self, context: SessionContext) -> Dict[str, Dict[str, Any]]:
        """Get all plugin data for rendering.
        
        This method is fast - it only reads from cache, no subprocess calls.
        
        Args:
            context: Session context
            
        Returns:
            Dictionary of plugin_name -> field_name -> value
        """
        data = {}
        
        for plugin_name, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
            
            try:
                plugin_data = plugin.get_cached(context)
                data[plugin_name] = plugin_data
            except Exception as e:
                logger.warning(f"Error getting cached data for {plugin_name}: {e}")
                data[plugin_name] = plugin._get_default_values()
        
        return data
    
    def unload_plugin(self, name: str) -> None:
        """Unload a plugin.
        
        Args:
            name: Plugin name
        """
        if name in self.plugins:
            del self.plugins[name]
            logger.info(f"Unloaded plugin: {name}")
