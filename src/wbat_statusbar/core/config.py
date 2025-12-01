"""Configuration system with TOML loading and validation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # Optional, only needed for writing config

from .logging import setup_logging

logger = setup_logging()


class ConfigError(Exception):
    """Configuration error."""


def get_config_path() -> Path:
    """Get the configuration file path.

    Tries ~/.config/wbat-iterm-status/config.toml first,
    then falls back to:
    ~/Library/Application Support/wbat-iterm-status/config.toml
    """
    # Try XDG config first
    xdg_config = Path.home() / ".config" / "wbat-iterm-status" / "config.toml"
    if xdg_config.exists():
        return xdg_config
    
    # Fallback to macOS Application Support
    app_support = Path.home() / "Library" / "Application Support" / "wbat-iterm-status" / "config.toml"
    if app_support.exists():
        return app_support
    
    # Default to XDG location for new installs
    return xdg_config


def get_default_config() -> Dict[str, Any]:
    """Generate default configuration."""
    return {
        "global": {
            "update_cadence_seconds": 1,
            "render_timeout_ms": 50,
            "log_level": "info",
        },
        "cycle": {
            "enabled": True,
            "interval_seconds": 8,
            "mode": "round_robin",
            "start_view": "default",
        },
        "views": {
            "default": {
                "template": "{path}  {git.summary}  {aws.short}  {gcp.short}",
            },
            "cloud": {
                "template": "{aws.long}  {gcp.long}",
            },
            "git": {
                "template": "{git.branch} {git.ahead_behind} {git.changes}",
            },
        },
        "plugins": {
            "git": {
                "enabled": True,
                "mode": "fast",
                "ttl_seconds": 2,
                "max_repo_scan_ms": 50,
            },
            "aws": {
                "enabled": True,
                "mode": "env_only",
                "ttl_seconds": 600,
                "source": "user_vars",
                "profile_var": "user.awsProfile",
                "region_var": "user.awsRegion",
            },
            "gcp": {
                "enabled": True,
                "mode": "env_only",
                "ttl_seconds": 600,
                "project_var": "user.gcpProject",
            },
            "kube": {
                "enabled": False,
                "ttl_seconds": 10,
            },
        },
    }


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from TOML file.
    
    Args:
        config_path: Optional path to config file. If None, uses default location.
    
    Returns:
        Configuration dictionary
    
    Raises:
        ConfigError: If config file is invalid or cannot be read
    """
    if config_path is None:
        config_path = get_config_path()
    
    # Create default config if file doesn't exist
    if not config_path.exists():
        logger.info(f"Config file not found at {config_path}, creating default config")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        default_config = get_default_config()
        if tomli_w is not None:
            with open(config_path, "wb") as f:
                tomli_w.dump(default_config, f)
        else:
            logger.warning("tomli_w not available, cannot write default config file")
        return default_config
    
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        raise ConfigError(f"Failed to load config from {config_path}: {e}") from e
    
    # Merge with defaults to ensure all keys exist
    default_config = get_default_config()
    merged_config = _merge_config(default_config, config)
    
    # Apply environment variable overrides
    merged_config = _apply_env_overrides(merged_config)
    
    # Validate configuration
    _validate_config(merged_config)
    
    return merged_config


def _merge_config(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user config into default config, recursively."""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to config.
    
    Environment variables:
    - WBAT_LOG_LEVEL: Override log_level
    - WBAT_UPDATE_CADENCE: Override update_cadence_seconds
    - WBAT_CYCLE_ENABLED: Override cycle.enabled (true/false)
    - WBAT_CYCLE_INTERVAL: Override cycle.interval_seconds
    """
    if "WBAT_LOG_LEVEL" in os.environ:
        config["global"]["log_level"] = os.environ["WBAT_LOG_LEVEL"].lower()
    
    if "WBAT_UPDATE_CADENCE" in os.environ:
        try:
            config["global"]["update_cadence_seconds"] = int(os.environ["WBAT_UPDATE_CADENCE"])
        except ValueError:
            logger.warning(f"Invalid WBAT_UPDATE_CADENCE value: {os.environ['WBAT_UPDATE_CADENCE']}")
    
    if "WBAT_CYCLE_ENABLED" in os.environ:
        config["cycle"]["enabled"] = os.environ["WBAT_CYCLE_ENABLED"].lower() in ("true", "1", "yes")
    
    if "WBAT_CYCLE_INTERVAL" in os.environ:
        try:
            config["cycle"]["interval_seconds"] = int(os.environ["WBAT_CYCLE_INTERVAL"])
        except ValueError:
            logger.warning(f"Invalid WBAT_CYCLE_INTERVAL value: {os.environ['WBAT_CYCLE_INTERVAL']}")
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration schema.
    
    Raises:
        ConfigError: If config is invalid
    """
    # Validate global section
    if "global" not in config:
        raise ConfigError("Missing 'global' section in config")
    
    global_section = config["global"]
    if "update_cadence_seconds" not in global_section:
        raise ConfigError("Missing 'update_cadence_seconds' in global section")
    update_cadence = global_section["update_cadence_seconds"]
    if not isinstance(update_cadence, int) or update_cadence < 1:
        raise ConfigError("'update_cadence_seconds' must be a positive integer")
    
    # Validate cycle section
    if "cycle" not in config:
        raise ConfigError("Missing 'cycle' section in config")
    
    cycle_section = config["cycle"]
    if "enabled" not in cycle_section:
        raise ConfigError("Missing 'enabled' in cycle section")
    if cycle_section.get("enabled") and "interval_seconds" not in cycle_section:
        raise ConfigError(
            "Missing 'interval_seconds' in cycle section when cycle is enabled"
        )
    
    # Validate views section
    if "views" not in config:
        raise ConfigError("Missing 'views' section in config")
    
    if not config["views"]:
        raise ConfigError("At least one view must be defined")
    
    for view_name, view_config in config["views"].items():
        if "template" not in view_config:
            raise ConfigError(f"View '{view_name}' missing 'template' field")
        template = view_config["template"]
        if not isinstance(template, str):
            raise ConfigError(f"View '{view_name}' template must be a string")
    
    # Validate plugins section
    if "plugins" not in config:
        raise ConfigError("Missing 'plugins' section in config")
    
    # Plugin-specific validation happens in plugin initialization
    logger.debug("Configuration validation passed")
