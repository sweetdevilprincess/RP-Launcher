"""Template cache with LRU eviction.

Provides efficient caching of loaded template files with Least Recently Used
eviction policy to manage memory usage.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any

from ...shared.logging import get_logger


class TemplateCache:
    """LRU cache for template data.

    This cache stores loaded template data in memory and automatically
    evicts the least recently used entries when the cache size limit
    is reached.

    The cache is thread-safe for read operations but not for concurrent
    writes. Use external synchronization if needed for write-heavy workloads.

    Example:
        >>> cache = TemplateCache(max_size=50)
        >>> cache.put(Path("fantasy.json"), {"genre": "Fantasy", "sections": {...}})
        >>> template = cache.get(Path("fantasy.json"))
        >>> template["genre"]
        "Fantasy"
    """

    def __init__(self, max_size: int = 100) -> None:
        """Initialize template cache.

        Args:
            max_size: Maximum number of templates to cache
        """
        self._max_size = max_size
        self._cache: OrderedDict[Path, Any] = OrderedDict()
        self._logger = get_logger(__name__)
        self._hits = 0
        self._misses = 0

    def get(self, key: Path) -> Any | None:
        """Get template data from cache.

        Moves the accessed item to the end (most recently used).

        Args:
            key: Template file path

        Returns:
            Cached template data, or None if not in cache
        """
        if key in self._cache:
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            self._hits += 1

            self._logger.debug(
                "template_cache.hit",
                context={
                    "key": str(key),
                    "cache_size": len(self._cache),
                    "hit_rate": self.hit_rate,
                },
            )

            return self._cache[key]

        self._misses += 1
        self._logger.debug(
            "template_cache.miss",
            context={
                "key": str(key),
                "cache_size": len(self._cache),
                "hit_rate": self.hit_rate,
            },
        )

        return None

    def put(self, key: Path, value: Any) -> None:
        """Put template data into cache.

        If cache is full, evicts the least recently used item.

        Args:
            key: Template file path
            value: Template data to cache
        """
        # If key already exists, remove it so we can re-add at the end
        if key in self._cache:
            del self._cache[key]

        # Add to end (most recently used)
        self._cache[key] = value

        # Evict LRU item if cache is full
        if len(self._cache) > self._max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            self._logger.debug(
                "template_cache.eviction",
                context={
                    "evicted_key": str(evicted_key),
                    "cache_size": len(self._cache),
                    "max_size": self._max_size,
                },
            )

    def invalidate(self, key: Path) -> bool:
        """Remove a template from the cache.

        Args:
            key: Template file path to invalidate

        Returns:
            True if key was in cache, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            self._logger.debug("template_cache.invalidated", context={"key": str(key)})
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._logger.info("template_cache.cleared", context={})

    @property
    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of items in cache
        """
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate as a percentage (0.0 to 1.0)
        """
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache stats (size, max_size, hits, misses, hit_rate)
        """
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
        }
