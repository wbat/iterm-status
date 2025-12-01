"""Main daemon entrypoint for iTerm2 status bar component."""

import asyncio
import signal
import sys
from typing import Dict, Optional

try:
    import iterm2
except ImportError:
    iterm2 = None
    print(
        "Error: iterm2 module not found. Please install it via: pip3 install iterm2",
        file=sys.stderr,
    )
    sys.exit(1)

from .core.cache import Cache
from .core.config import load_config
from .core.logging import setup_logging
from .core.plugin_manager import PluginManager
from .core.render import Renderer, ViewCycler
from .core.scheduler import Scheduler
from .iterm.components import ComponentRegistry
from .iterm.session_vars import SessionContextCollector

logger = setup_logging()


class StatusBarDaemon:
    """Main daemon that manages the status bar component."""

    def __init__(self):
        self.connection = None  # iterm2.Connection when available
        self.config: Optional[Dict] = None
        self.cache: Optional[Cache] = None
        self.scheduler: Optional[Scheduler] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.renderer: Optional[Renderer] = None
        self.view_cycler: Optional[ViewCycler] = None
        self.component_registry: Optional[ComponentRegistry] = None
        self.context_collector: Optional[SessionContextCollector] = None
        self._running = False
        self._current_session_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize all components."""
        # Load configuration
        try:
            self.config = load_config()
            log_level = self.config["global"].get("log_level", "info")
            setup_logging(log_level=log_level)
            logger.info("Configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}", exc_info=True)
            sys.exit(1)

        # Initialize core components
        self.cache = Cache()
        self.scheduler = Scheduler()
        await self.scheduler.start()

        # Initialize plugin manager
        self.plugin_manager = PluginManager(
            config=self.config, cache=self.cache, scheduler=self.scheduler
        )
        self.plugin_manager.load_plugins()

        # Initialize renderer
        cycle_config = self.config.get("cycle", {})
        self.view_cycler = ViewCycler(
            views=self.config.get("views", {}),
            enabled=cycle_config.get("enabled", True),
            interval_seconds=cycle_config.get("interval_seconds", 8.0),
            mode=cycle_config.get("mode", "round_robin"),
            start_view=cycle_config.get("start_view", "default"),
        )

        self.renderer = Renderer(
            views=self.config.get("views", {}),
            view_cycler=self.view_cycler,
            render_timeout_ms=self.config["global"].get("render_timeout_ms", 50),
        )

        logger.info("Components initialized")

    async def connect(self) -> None:
        """Connect to iTerm2."""
        try:
            self.connection = await iterm2.Connection.async_create()
            logger.info("Connected to iTerm2")
        except Exception as e:
            logger.error(f"Failed to connect to iTerm2: {e}", exc_info=True)
            sys.exit(1)

    async def setup_components(self) -> None:
        """Set up iTerm2 components and context collection."""
        if not self.connection:
            raise RuntimeError("Not connected to iTerm2")

        # Initialize component registry
        self.component_registry = ComponentRegistry(self.connection)

        # Initialize context collector
        self.context_collector = SessionContextCollector(self.connection)
        await self.context_collector.start()

        # Register status bar component
        update_cadence = self.config["global"].get("update_cadence_seconds", 1.0)

        await self.component_registry.register_component(
            component_id="wbat-status",
            short_description="WBAT Status",
            detailed_description="Customizable status bar with git, AWS, GCP, and more",
            render_func=self._render_status_bar,
            update_cadence=update_cadence,
            knobs={
                "cycle_enabled": self.config.get("cycle", {}).get("enabled", True),
                "cycle_interval": self.config.get("cycle", {}).get("interval_seconds", 8),
            },
        )

        logger.info("Status bar component registered")

    def _render_status_bar(self) -> str:
        """Render the status bar text (called by iTerm2).

        This method must be fast - no subprocess calls, only cache reads.
        """
        if not self._current_session_id:
            return ""

        # Get current context
        context = self.context_collector.get_context(self._current_session_id)
        if not context:
            return ""

        # Get plugin data (from cache only)
        plugin_data = self.plugin_manager.get_plugin_data(context)

        # Build context for renderer
        render_context = {
            "command": context.command_line,
            "job": context.job_name,
        }

        # Render
        try:
            return self.renderer.render(plugin_data=plugin_data, context=render_context)
        except Exception as e:
            logger.error(f"Error rendering status bar: {e}", exc_info=True)
            return f"[error: {e}]"

    async def update_component(self) -> None:
        """Update the status bar component."""
        if not self.component_registry:
            return

        # Get current session
        app = await iterm2.async_get_app(self.connection)
        current_session = app.current_terminal_window.current_tab.current_session

        if current_session:
            self._current_session_id = current_session.session_id

            # Register plugin tasks for this session if not already done
            context = self.context_collector.get_context(self._current_session_id)
            if context:
                # Check if tasks are already registered (simple check)
                task_status = self.scheduler.get_all_task_status()
                task_prefix = f"git:{self._current_session_id}"
                if not any(k.startswith(task_prefix) for k in task_status.keys()):
                    await self.plugin_manager.register_plugin_tasks(context)

        # Update component display
        await self.component_registry.update_component("wbat-status")

    async def run(self) -> None:
        """Main daemon loop."""
        self._running = True

        # Set up signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self._running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Initial update
        await self.update_component()

        # Main loop
        update_cadence = self.config["global"].get("update_cadence_seconds", 1.0)

        while self._running:
            try:
                await self.update_component()

                # Cleanup expired cache entries periodically
                if self.cache:
                    self.cache.cleanup_expired()

                await asyncio.sleep(update_cadence)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def shutdown(self) -> None:
        """Shutdown the daemon gracefully."""
        logger.info("Shutting down daemon...")

        if self.scheduler:
            await self.scheduler.stop()

        if self.cache:
            self.cache.invalidate()

        logger.info("Daemon shut down")


async def main():
    """Main entry point."""
    daemon = StatusBarDaemon()

    try:
        await daemon.initialize()
        await daemon.connect()
        await daemon.setup_components()
        await daemon.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await daemon.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
