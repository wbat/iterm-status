"""GCP plugin with env-only and identity modes, background CLI calls."""

from typing import Any, Dict, List, Optional

from ..iterm.session_vars import SessionContext
from ..util.subprocess import run_command_safe
from .base import BasePlugin


class GCPPlugin(BasePlugin):
    """GCP plugin providing project and account information."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = self.config.get("mode", "env_only")
        self.project_var = self.config.get("project_var", "user.gcpProject")
        self._last_account: str = ""
    
    def get_fields(self) -> List[str]:
        return ["project", "account", "short", "long"]
    
    def get_dependencies(self) -> List[str]:
        if self.mode == "identity":
            return ["gcloud"]
        return []
    
    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update GCP plugin data."""
        # Get project from user vars
        project = context.get_user_var(self.project_var)
        
        data = {
            "project": project,
            "account": "",
            "short": "",
            "long": "",
        }
        
        # Build short format
        if project:
            data["short"] = f"GCP:{project}"
        
        # Identity mode: get account
        if self.mode == "identity":
            try:
                account = await run_command_safe(
                    "gcloud config get-value account",
                    timeout=5.0,
                    default=""
                )
                if account:
                    data["account"] = account.strip()
                    self._last_account = data["account"]
            except Exception as e:
                self.set_error(e)
                # Use last known good value
                data["account"] = self._last_account
        else:
            # Use last known good account if available
            data["account"] = self._last_account
        
        # Build long format
        long_parts = []
        if project:
            long_parts.append(f"project:{project}")
        if data["account"]:
            long_parts.append(f"account:{data['account']}")
        data["long"] = " ".join(long_parts) if long_parts else ""
        
        self._set_cached(context, data)
        return data
