"""Base plugin interface with field declaration, dependencies, and TTL configuration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core.cache import Cache
from ..core.logging import setup_logging
from ..core.scheduler import Scheduler
from ..iterm.session_vars import SessionContext
from ..util.subprocess import check_command_exists

logger = setup_logging()


class PluginError(Exception):
    """Plugin error."""


class BasePlugin(ABC):
    """Base class for all status bar plugins."""

    def __init__(self, name: str, config: Dict[str, Any], cache: Cache, scheduler: Scheduler):
        self.name = name
        self.config = config
        self.cache = cache
        self.scheduler = scheduler
        self.enabled = config.get("enabled", True)
        self.ttl_seconds = config.get("ttl_seconds", 60)
        self._last_error: Optional[Exception] = None

    @abstractmethod
    def get_fields(self) -> List[str]:
        """Get list of field names this plugin provides.

        Returns:
            List of field names (e.g., ["branch", "summary", "ahead_behind"])
        """
        pass

    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get list of dependencies (CLI tools, env vars).

        Returns:
            List of dependency names (e.g., ["git", "aws"])
        """
        pass

    def check_dependencies(self) -> bool:
        """Check if all dependencies are available.

        Returns:
            True if all dependencies are available
        """
        dependencies = self.get_dependencies()
        for dep in dependencies:
            if not check_command_exists(dep):
                logger.debug(f"Plugin {self.name} missing dependency: {dep}")
                return False
        return True

    @abstractmethod
    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update plugin data for a session context.

        This method is called in the background by the scheduler.
        It should perform any expensive operations (subprocess calls, etc.)
        and return a dictionary of field_name -> value.

        Args:
            context: Current session context

        Returns:
            Dictionary of field_name -> value
        """
        pass

    def get_cached(self, context: SessionContext) -> Dict[str, Any]:
        """Get cached plugin data for a session context.

        This method is called during render (must be fast, no subprocess calls).
        It returns the last known good value from cache.

        Args:
            context: Current session context

        Returns:
            Dictionary of field_name -> value
        """
        cache_key = self._get_cache_key(context)
        cached = self.cache.get(cache_key)

        if cached is None:
            # Return empty/default values
            return self._get_default_values()

        return cached

    def _get_cache_key(self, context: SessionContext) -> str:
        """Generate cache key for this plugin and context.

        Args:
            context: Session context

        Returns:
            Cache key string
        """
        identity_inputs = context.get_identity_inputs()
        base_key = self.cache.get_cache_key(context.session_id, context.path, identity_inputs)
        return f"{self.name}:{base_key}"

    def _get_default_values(self) -> Dict[str, Any]:
        """Get default values for all fields.

        Returns:
            Dictionary of field_name -> default value
        """
        return {field: "" for field in self.get_fields()}

    def _set_cached(self, context: SessionContext, data: Dict[str, Any]) -> None:
        """Store plugin data in cache.

        Args:
            context: Session context
            data: Data to cache
        """
        cache_key = self._get_cache_key(context)
        self.cache.set(cache_key, data, self.ttl_seconds)

    def get_last_error(self) -> Optional[Exception]:
        """Get the last error that occurred during update.

        Returns:
            Exception or None
        """
        return self._last_error

    def set_error(self, error: Exception) -> None:
        """Record an error that occurred during update.

        Args:
            error: Exception that occurred
        """
        self._last_error = error
        logger.warning(f"Plugin {self.name} error: {error}")
