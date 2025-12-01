# Plugin Development Guide

Learn how to create custom plugins for WBAT iTerm2 Status Bar.

## Plugin Interface

All plugins inherit from `BasePlugin`:

```python
from wbat_statusbar.plugins.base import BasePlugin
from wbat_statusbar.iterm.session_vars import SessionContext
from typing import Dict, List, Any

class MyPlugin(BasePlugin):
    def get_fields(self) -> List[str]:
        """Return list of field names this plugin provides."""
        return ["field1", "field2"]
    
    def get_dependencies(self) -> List[str]:
        """Return list of CLI tools or dependencies needed."""
        return ["my-tool"]
    
    async def update(self, context: SessionContext) -> Dict[str, Any]:
        """Update plugin data (called in background)."""
        # Expensive operations here (subprocess calls, etc.)
        return {
            "field1": "value1",
            "field2": "value2",
        }
```

## Key Methods

### `get_fields()`
Returns list of field names this plugin provides. These can be referenced in view templates as `{plugin_name.field_name}`.

### `get_dependencies()`
Returns list of CLI tools or other dependencies. The plugin manager will check if these are available.

### `update(context)`
Called periodically by the scheduler. This is where you do expensive operations:
- Subprocess calls
- Network requests
- File I/O
- Database queries

**Important**: This method runs in the background. Never block the render path.

### `get_cached(context)`
Called during render (must be fast). Returns cached data or default values. The base class handles caching automatically.

## Example: Simple Plugin

```python
from wbat_statusbar.plugins.base import BasePlugin
from wbat_statusbar.iterm.session_vars import SessionContext
from wbat_statusbar.util.subprocess import run_command_safe
from typing import Dict, List

class DatePlugin(BasePlugin):
    def get_fields(self) -> List[str]:
        return ["date", "time"]
    
    def get_dependencies(self) -> List[str]:
        return []  # No external dependencies
    
    async def update(self, context: SessionContext) -> Dict[str, Any]:
        import datetime
        now = datetime.datetime.now()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }
```

## Example: Plugin with Subprocess

```python
from wbat_statusbar.plugins.base import BasePlugin
from wbat_statusbar.iterm.session_vars import SessionContext
from wbat_statusbar.util.subprocess import run_command_safe
from typing import Dict, List

class NodeVersionPlugin(BasePlugin):
    def get_fields(self) -> List[str]:
        return ["version"]
    
    def get_dependencies(self) -> List[str]:
        return ["node"]
    
    async def update(self, context: SessionContext) -> Dict[str, Any]:
        version = await run_command_safe(
            "node --version",
            timeout=2.0,
            default="unknown"
        )
        return {"version": version.strip()}
```

## Configuration

Plugins receive configuration from the config file:

```toml
[plugins.my_plugin]
enabled = true
ttl_seconds = 60
custom_setting = "value"
```

Access via `self.config`:
```python
custom_setting = self.config.get("custom_setting", "default")
```

## Caching

The base class handles caching automatically:
- Data is cached with TTL from `self.ttl_seconds`
- Cache key includes session ID, path, and identity inputs
- Use `self._set_cached(context, data)` to store data
- Use `self.get_cached(context)` to retrieve (or override for custom logic)

## Error Handling

Handle errors gracefully:

```python
async def update(self, context: SessionContext) -> Dict[str, Any]:
    try:
        result = await expensive_operation()
        return {"field": result}
    except Exception as e:
        self.set_error(e)  # Record error
        # Return last known good value or defaults
        return self.get_cached(context) or self._get_default_values()
```

## Best Practices

1. **Fast Render Path**: `get_cached()` must be fast - no subprocess calls
2. **Background Updates**: All expensive operations in `update()`
3. **Error Handling**: Always return valid data, even on error
4. **TTL Management**: Use appropriate TTLs (short for dynamic data, long for static)
5. **Dependency Checking**: Declare all dependencies in `get_dependencies()`
6. **Default Values**: Provide sensible defaults for all fields

## Registering Plugins

Built-in plugins are registered in `plugin_manager.py`:

```python
BUILTIN_PLUGINS = {
    "my_plugin": MyPlugin,
}
```

For user plugins (future feature), plugins will be loaded from a plugins directory.

## Testing Plugins

Create unit tests:

```python
import pytest
from wbat_statusbar.plugins.my_plugin import MyPlugin
from wbat_statusbar.core.cache import Cache
from wbat_statusbar.core.scheduler import Scheduler

@pytest.fixture
def plugin():
    config = {"enabled": True, "ttl_seconds": 60}
    cache = Cache()
    scheduler = Scheduler()
    return MyPlugin("my_plugin", config, cache, scheduler)

@pytest.mark.asyncio
async def test_plugin_update(plugin):
    context = SessionContext("session-1", path="/tmp")
    data = await plugin.update(context)
    assert "field1" in data
```

## Advanced: Context Overrides

Plugins can trigger view overrides:

```python
# In your plugin
if some_condition:
    # This would be handled by the renderer
    # (future feature)
    pass
```

## See Also

- [Base Plugin Source](../src/wbat_statusbar/plugins/base.py)
- [Example Plugins](../src/wbat_statusbar/plugins/)
- [Configuration Guide](configuration.md)
