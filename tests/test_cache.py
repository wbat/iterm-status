"""Tests for cache system."""

import time

from wbat_statusbar.core.cache import Cache


def test_cache_set_get():
    """Test basic cache set/get."""
    cache = Cache()

    cache.set("key1", "value1", ttl_seconds=60)
    assert cache.get("key1") == "value1"


def test_cache_expiration():
    """Test cache expiration."""
    cache = Cache()

    cache.set("key1", "value1", ttl_seconds=0.1)
    assert cache.get("key1") == "value1"

    time.sleep(0.2)
    assert cache.get("key1") is None


def test_cache_key_generation():
    """Test cache key generation."""
    cache = Cache()

    key = cache.get_cache_key(
        session_id="session-1", path="/tmp/test", identity_inputs={"aws_profile": "prod"}
    )

    assert "session-1" in key
    assert "/tmp/test" in key
    assert "aws_profile" in key


def test_fast_cache():
    """Test fast cache operations."""
    cache = Cache()

    cache.set_fast("key1", "rendered_string")
    assert cache.get_fast("key1") == "rendered_string"


def test_cache_invalidation():
    """Test cache invalidation."""
    cache = Cache()

    cache.set("key1", "value1", ttl_seconds=60)
    cache.set("key2", "value2", ttl_seconds=60)

    cache.invalidate("key1")
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"

    cache.invalidate()  # Clear all
    assert cache.get("key2") is None


def test_cache_cleanup_expired():
    """Test cleanup of expired entries."""
    cache = Cache()

    cache.set("key1", "value1", ttl_seconds=0.1)
    cache.set("key2", "value2", ttl_seconds=60)

    time.sleep(0.2)

    removed = cache.cleanup_expired()
    assert removed == 1
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
