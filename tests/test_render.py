"""Tests for render engine."""

from wbat_statusbar.core.render import Renderer, ViewCycler


def test_view_cycler():
    """Test view cycler."""
    views = {
        "default": {"template": "{path}"},
        "git": {"template": "{git.branch}"},
    }
    
    cycler = ViewCycler(
        views=views,
        enabled=True,
        interval_seconds=0.1,
        mode="round_robin",
        start_view="default"
    )
    
    assert cycler.get_current_view() == "default"


def test_renderer_template_resolution():
    """Test template resolution."""
    views = {
        "default": {"template": "{path} {git.branch}"},
    }
    
    cycler = ViewCycler(views=views, enabled=False)
    renderer = Renderer(views=views, view_cycler=cycler)
    
    plugin_data = {
        "core": {"path": "/tmp/test"},
        "git": {"branch": "main"},
    }
    
    result = renderer.render(plugin_data=plugin_data)
    assert "/tmp/test" in result
    assert "main" in result


def test_renderer_field_extraction():
    """Test field extraction from template."""
    views = {
        "default": {"template": "{path} {git.branch} {aws.short}"},
    }
    
    cycler = ViewCycler(views=views, enabled=False)
    renderer = Renderer(views=views, view_cycler=cycler)
    
    fields = renderer.extract_fields(views["default"]["template"])
    assert "path" in fields
    assert "git.branch" in fields
    assert "aws.short" in fields


def test_renderer_nested_fields():
    """Test nested field access."""
    views = {
        "default": {"template": "{git.summary}"},
    }
    
    cycler = ViewCycler(views=views, enabled=False)
    renderer = Renderer(views=views, view_cycler=cycler)
    
    plugin_data = {
        "git": {"summary": "main +2"},
    }
    
    result = renderer.render(plugin_data=plugin_data)
    assert "main +2" in result
