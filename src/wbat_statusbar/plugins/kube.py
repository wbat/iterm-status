"""Kube plugin for context and namespace detection."""

import re
from typing import Any, Dict, List

from ..iterm.session_vars import SessionContext
from ..util.subprocess import run_command_safe
from .base import BasePlugin


class KubePlugin(BasePlugin):
    """Kubernetes plugin providing context and namespace information."""
    
    def get_fields(self) -> List[str]:
        return ["context", "namespace", "short", "long"]
    
    def get_dependencies(self) -> List[str]:
        return ["kubectl"]
    
    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update Kubernetes plugin data."""
        # Get context from kubectl config
        kube_context = await run_command_safe(
            "kubectl config current-context",
            timeout=2.0,
            default=""
        )
        
        # Get namespace from kubectl config
        namespace = await run_command_safe(
            "kubectl config view --minify --output 'jsonpath={..namespace}'",
            timeout=2.0,
            default=""
        )
        
        # If no namespace from config, try to get from current context
        if not namespace and kube_context:
            # Try to extract namespace from context name (common pattern: context-namespace)
            if "/" in kube_context:
                parts = kube_context.split("/")
                if len(parts) > 1:
                    namespace = parts[-1]
        
        data = {
            "context": kube_context.strip() if kube_context else "",
            "namespace": namespace.strip() if namespace else "",
            "short": "",
            "long": "",
        }
        
        # Build short format
        short_parts = []
        if kube_context:
            # Shorten context name
            context_short = kube_context.split("/")[-1] if "/" in kube_context else kube_context
            short_parts.append(f"k8s:{context_short[:20]}")
        if namespace:
            short_parts.append(f"ns:{namespace[:15]}")
        data["short"] = " ".join(short_parts) if short_parts else ""
        
        # Build long format
        long_parts = []
        if kube_context:
            long_parts.append(f"context:{kube_context}")
        if namespace:
            long_parts.append(f"namespace:{namespace}")
        data["long"] = " ".join(long_parts) if long_parts else ""
        
        self._set_cached(context, data)
        return data
