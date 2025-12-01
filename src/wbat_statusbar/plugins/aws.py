"""AWS plugin with env-only and identity modes, background CLI calls."""

import json
from typing import Any, Dict, List

from ..iterm.session_vars import SessionContext
from ..util.subprocess import run_command_safe
from .base import BasePlugin


class AWSPlugin(BasePlugin):
    """AWS plugin providing profile, region, and identity information."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = self.config.get("mode", "env_only")
        self.profile_var = self.config.get("profile_var", "user.awsProfile")
        self.region_var = self.config.get("region_var", "user.awsRegion")
        self._last_identity: Dict[str, Any] = {}

    def get_fields(self) -> List[str]:
        return ["profile", "region", "account", "role", "short", "long"]

    def get_dependencies(self) -> List[str]:
        if self.mode == "identity":
            return ["aws"]
        return []

    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update AWS plugin data."""
        # Get profile and region from user vars
        profile = context.get_user_var(self.profile_var)
        region = context.get_user_var(self.region_var)

        data = {
            "profile": profile,
            "region": region,
            "account": "",
            "role": "",
            "short": "",
            "long": "",
        }

        # Build short format
        short_parts = []
        if profile:
            short_parts.append(f"AWS:{profile}")
        if region:
            short_parts.append(region)
        data["short"] = " ".join(short_parts) if short_parts else ""

        # Identity mode: get account and role
        if self.mode == "identity" and profile:
            try:
                identity_output = await run_command_safe(
                    f"aws sts get-caller-identity --profile {profile} --output json",
                    timeout=5.0,
                    default="",
                )

                if identity_output:
                    identity = json.loads(identity_output)
                    account = identity.get("Account", "")
                    arn = identity.get("Arn", "")

                    # Extract role from ARN
                    role = ""
                    if arn:
                        # ARN format: arn:aws:sts::ACCOUNT:assumed-role/ROLE/SESSION
                        if "/" in arn:
                            role = arn.split("/")[-1].split("/")[0]
                        elif ":" in arn:
                            parts = arn.split(":")
                            if len(parts) > 5:
                                role = parts[5]

                    data["account"] = account
                    data["role"] = role
                    self._last_identity = data
            except json.JSONDecodeError:
                # Use last known good value
                data.update(self._last_identity)
            except Exception as e:
                self.set_error(e)
                # Use last known good value
                data.update(self._last_identity)
        else:
            # Use last known good identity if available
            if self._last_identity:
                data["account"] = self._last_identity.get("account", "")
                data["role"] = self._last_identity.get("role", "")

        # Build long format
        long_parts = []
        if profile:
            long_parts.append(f"profile:{profile}")
        if region:
            long_parts.append(f"region:{region}")
        if data["account"]:
            long_parts.append(f"account:{data['account']}")
        if data["role"]:
            long_parts.append(f"role:{data['role']}")
        data["long"] = " ".join(long_parts) if long_parts else ""

        self._set_cached(context, data)
        return data
