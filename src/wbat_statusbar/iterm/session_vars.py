"""Read iTerm2 session variables and user.* vars with VariableMonitor."""

import asyncio
from typing import Any, Callable, Dict, Optional

try:
    import iterm2
except ImportError:
    iterm2 = None  # Optional for testing

from ..core.logging import setup_logging

logger = setup_logging()


class SessionContext:
    """Session context data collected from iTerm2."""
    
    def __init__(
        self,
        session_id: str,
        path: str = "",
        command_line: str = "",
        job_name: str = "",
        user_vars: Optional[Dict[str, str]] = None
    ):
        self.session_id = session_id
        self.path = path
        self.command_line = command_line
        self.job_name = job_name
        self.user_vars = user_vars or {}
    
    def get_user_var(self, name: str, default: str = "") -> str:
        """Get a user variable value.
        
        Args:
            name: Variable name (e.g., "awsProfile" or "user.awsProfile")
            default: Default value if not found
            
        Returns:
            Variable value or default
        """
        # Handle both "awsProfile" and "user.awsProfile" formats
        if name.startswith("user."):
            name = name[5:]  # Remove "user." prefix
        
        return self.user_vars.get(name, default)
    
    def get_identity_inputs(self) -> Dict[str, str]:
        """Get identity-related inputs for cache key generation.
        
        Returns:
            Dictionary of identity inputs (aws profile, gcp project, etc.)
        """
        inputs = {}
        
        aws_profile = self.get_user_var("awsProfile")
        if aws_profile:
            inputs["aws_profile"] = aws_profile
        
        aws_region = self.get_user_var("awsRegion")
        if aws_region:
            inputs["aws_region"] = aws_region
        
        gcp_project = self.get_user_var("gcpProject")
        if gcp_project:
            inputs["gcp_project"] = gcp_project
        
        return inputs


class SessionContextCollector:
    """Collects session context from iTerm2 with reactive updates."""
    
    def __init__(self, connection):
        self.connection = connection
        self._contexts: Dict[str, SessionContext] = {}
        self._monitors: Dict[str, Any] = {}  # iterm2.VariableMonitor when available
        self._callbacks: Dict[str, Callable[[SessionContext], None]] = {}
    
    async def start(self) -> None:
        """Start monitoring session variables."""
        if iterm2 is None:
            logger.warning("iterm2 not available, session monitoring disabled")
            return
        app = await iterm2.async_get_app(self.connection)
        
        # Monitor all sessions
        async def on_new_session(session) -> None:
            await self._monitor_session(session)
        
        # Get existing sessions
        for window in app.windows:
            for tab in window.tabs:
                for session in tab.sessions:
                    await self._monitor_session(session)
        
        # Listen for new sessions
        async def monitor():
            async with iterm2.NewSessionMonitor(self.connection) as mon:
                async for session_id in mon:
                    session = app.get_session_by_id(session_id)
                    if session:
                        await self._monitor_session(session)
        
        asyncio.create_task(monitor())
        logger.info("Session context collector started")
    
    async def _monitor_session(self, session) -> None:
        """Start monitoring a specific session.
        
        Args:
            session: iTerm2 session to monitor
        """
        session_id = session.session_id
        
        # Create initial context
        context = await self._collect_context(session)
        self._contexts[session_id] = context
        
        # Set up variable monitor for reactive updates
        async def variable_changed(
            name: str,
            value: Optional[str]
        ) -> None:
            # Update context
            context = await self._collect_context(session)
            self._contexts[session_id] = context
            
            # Call callback if registered
            callback = self._callbacks.get(session_id)
            if callback:
                try:
                    callback(context)
                except Exception as e:
                    logger.error(f"Error in context callback: {e}", exc_info=True)
        
        # Monitor key variables
        if iterm2 is None:
            return
        monitor = await iterm2.VariableMonitor.async_create(
            self.connection,
            variable_names=[
                "session.path",
                "session.commandLine",
                "session.jobName",
            ],
            session_id=session_id,
            callback=variable_changed
        )
        
        self._monitors[session_id] = monitor
        
        # Also monitor user.* variables (these change less frequently)
        user_var_patterns = [
            "user.awsProfile",
            "user.awsRegion",
            "user.gcpProject",
            "user.kubeContext",
        ]
        
        for var_name in user_var_patterns:
            try:
                await iterm2.VariableMonitor.async_create(
                    self.connection,
                    variable_names=[var_name],
                    session_id=session_id,
                    callback=variable_changed
                )
                # Store additional monitors (iTerm2 handles cleanup)
            except Exception as e:
                logger.debug(f"Could not monitor {var_name}: {e}")
        
        logger.debug(f"Started monitoring session: {session_id}")
    
    async def _collect_context(self, session) -> SessionContext:
        """Collect context from a session.
        
        Args:
            session: iTerm2 session
            
        Returns:
            SessionContext object
        """
        session_id = session.session_id
        
        # Get session variables
        try:
            path = await session.async_get_variable("path") or ""
            command_line = await session.async_get_variable("commandLine") or ""
            job_name = await session.async_get_variable("jobName") or ""
        except Exception as e:
            logger.warning(f"Error reading session variables: {e}")
            path = ""
            command_line = ""
            job_name = ""
        
        # Get user variables
        user_vars = {}
        user_var_names = [
            "awsProfile",
            "awsRegion",
            "gcpProject",
            "kubeContext",
            "gitInfo",
            "wbatStatus",
        ]
        
        for var_name in user_var_names:
            try:
                value = await session.async_get_variable(f"user.{var_name}")
                if value:
                    user_vars[var_name] = value
            except Exception:
                pass  # Variable may not exist
        
        return SessionContext(
            session_id=session_id,
            path=path,
            command_line=command_line,
            job_name=job_name,
            user_vars=user_vars
        )
    
    def get_context(self, session_id: str) -> Optional[SessionContext]:
        """Get current context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionContext or None if not found
        """
        return self._contexts.get(session_id)
    
    def register_callback(
        self,
        session_id: str,
        callback: Callable[[SessionContext], None]
    ) -> None:
        """Register a callback for context changes.
        
        Args:
            session_id: Session identifier
            callback: Function to call when context changes
        """
        self._callbacks[session_id] = callback
    
    def unregister_callback(self, session_id: str) -> None:
        """Unregister a callback.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._callbacks:
            del self._callbacks[session_id]
