"""TTL-based cache with per-session keys and fast/slow cache separation."""

import threading
import time
from typing import Any, Dict, Optional, Tuple


class CacheEntry:
    """A cache entry with TTL and metadata."""
    
    def __init__(self, value: Any, ttl_seconds: float, created_at: Optional[float] = None):
        self.value = value
        self.ttl_seconds = ttl_seconds
        self.created_at = created_at or time.time()
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at
    
    def time_until_expiry(self) -> float:
        """Get seconds until expiry."""
        return max(0, self.ttl_seconds - self.age())


class Cache:
    """Thread-safe TTL-based cache with per-session keys.
    
    Cache keys are formatted as: {session_id}:{path}:{identity_inputs}
    """
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._fast_cache: Dict[str, str] = {}  # Pre-rendered strings for fast access
        self._fast_cache_lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            entry.last_accessed = time.time()
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl_seconds)
    
    def get_fast(self, key: str) -> Optional[str]:
        """Get pre-rendered string from fast cache.
        
        Fast cache is for final rendered strings that don't need
        any processing - just return immediately.
        
        Args:
            key: Cache key
            
        Returns:
            Cached string or None if not found
        """
        with self._fast_cache_lock:
            return self._fast_cache.get(key)
    
    def set_fast(self, key: str, value: str) -> None:
        """Set pre-rendered string in fast cache.
        
        Args:
            key: Cache key
            value: Pre-rendered string
        """
        with self._fast_cache_lock:
            self._fast_cache[key] = value
    
    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry or all entries.
        
        Args:
            key: Specific key to invalidate, or None to clear all
        """
        with self._lock:
            if key is None:
                self._cache.clear()
            elif key in self._cache:
                del self._cache[key]
        
        with self._fast_cache_lock:
            if key is None:
                self._fast_cache.clear()
            elif key in self._fast_cache:
                del self._fast_cache[key]
    
    def invalidate_by_prefix(self, prefix: str) -> None:
        """Invalidate all cache entries with given prefix.
        
        Useful for invalidating all entries for a session or plugin.
        
        Args:
            prefix: Key prefix to match
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache[key]
        
        with self._fast_cache_lock:
            keys_to_remove = [k for k in self._fast_cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._fast_cache[key]
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def get_cache_key(
        self,
        session_id: str,
        path: str,
        identity_inputs: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate cache key from session context.
        
        Args:
            session_id: iTerm2 session ID
            path: Current working directory path
            identity_inputs: Dictionary of identity-related inputs (e.g., aws profile)
            
        Returns:
            Cache key string
        """
        parts = [session_id, path]
        
        if identity_inputs:
            # Sort for consistent key generation
            identity_str = ":".join(
                f"{k}={v}" for k, v in sorted(identity_inputs.items())
            )
            parts.append(identity_str)
        
        return ":".join(parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(1 for entry in self._cache.values() if entry.is_expired())
            active_entries = total_entries - expired_count
        
        with self._fast_cache_lock:
            fast_cache_size = len(self._fast_cache)
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_count,
            "fast_cache_size": fast_cache_size,
        }
