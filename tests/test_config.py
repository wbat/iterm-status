"""Tests for configuration system."""

from wbat_statusbar.core.config import (
    get_default_config,
    load_config,
)


def test_get_default_config():
    """Test default config generation."""
    config = get_default_config()
    
    assert "global" in config
    assert "views" in config
    assert "plugins" in config
    assert config["global"]["update_cadence_seconds"] == 1
    assert "default" in config["views"]


def test_load_config_creates_default(tmp_path):
    """Test that load_config creates default config if missing."""
    config_dir = tmp_path / "wbat-iterm-status"
    config_file = config_dir / "config.toml"
    
    # Config file doesn't exist yet
    assert not config_file.exists()
    
    # Monkey patch get_config_path to use our temp dir
    import wbat_statusbar.core.config as config_module
    original_get_path = config_module.get_config_path
    
    def mock_get_path():
        return config_file
    
    config_module.get_config_path = mock_get_path
    
    try:
        config = load_config()
        assert config_file.exists()
        assert "global" in config
    finally:
        config_module.get_config_path = original_get_path


def test_config_validation():
    """Test config validation."""
    # This would test validation logic
    # For now, just verify default config is valid
    config = get_default_config()
    assert config is not None


def test_env_overrides(tmp_path, monkeypatch):
    """Test environment variable overrides."""
    config_dir = tmp_path / "wbat-iterm-status"
    config_file = config_dir / "config.toml"
    config_dir.mkdir(parents=True)
    
    # Create minimal config
    config_file.write_text("""
[global]
update_cadence_seconds = 1
log_level = "info"

[cycle]
enabled = true
interval_seconds = 8

[views.default]
template = "{path}"

[plugins.git]
enabled = true
""")
    
    import wbat_statusbar.core.config as config_module
    original_get_path = config_module.get_config_path
    
    def mock_get_path():
        return config_file
    
    config_module.get_config_path = mock_get_path
    
    try:
        # Test log level override
        monkeypatch.setenv("WBAT_LOG_LEVEL", "debug")
        config = load_config()
        assert config["global"]["log_level"] == "debug"
        
        # Test update cadence override
        monkeypatch.setenv("WBAT_UPDATE_CADENCE", "5")
        config = load_config()
        assert config["global"]["update_cadence_seconds"] == 5
    finally:
        config_module.get_config_path = original_get_path
