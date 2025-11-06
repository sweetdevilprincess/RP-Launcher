"""Unit tests for TemplateCache.

Tests LRU cache functionality with:
- Basic get/put operations
- LRU eviction policy
- Cache invalidation
- Hit/miss tracking
- Statistics
"""

from pathlib import Path

import pytest
from refactoring.src.automation.templates.template_cache import TemplateCache


class TestBasicOperations:
    """Test basic cache operations."""

    def test_get_empty_cache_returns_none(self):
        """Test get returns None when cache is empty."""
        cache = TemplateCache(max_size=10)
        key = Path("template.json")

        result = cache.get(key)

        assert result is None

    def test_put_and_get(self):
        """Test putting and getting a value."""
        cache = TemplateCache(max_size=10)
        key = Path("template.json")
        value = {"genre": "Fantasy", "sections": {}}

        cache.put(key, value)
        result = cache.get(key)

        assert result == value

    def test_put_multiple_items(self):
        """Test putting multiple items."""
        cache = TemplateCache(max_size=10)
        items = {
            Path("template1.json"): {"genre": "Fantasy"},
            Path("template2.json"): {"genre": "Sci-Fi"},
            Path("template3.json"): {"genre": "Mystery"},
        }

        for key, value in items.items():
            cache.put(key, value)

        # All should be retrievable
        for key, expected_value in items.items():
            assert cache.get(key) == expected_value

    def test_update_existing_key(self):
        """Test updating an existing key with new value."""
        cache = TemplateCache(max_size=10)
        key = Path("template.json")

        cache.put(key, {"genre": "Fantasy"})
        cache.put(key, {"genre": "Sci-Fi"})

        result = cache.get(key)
        assert result == {"genre": "Sci-Fi"}

    def test_get_nonexistent_key(self):
        """Test getting a key that was never added."""
        cache = TemplateCache(max_size=10)

        cache.put(Path("exists.json"), {"genre": "Fantasy"})
        result = cache.get(Path("notfound.json"))

        assert result is None


class TestLRUEviction:
    """Test LRU eviction policy."""

    def test_eviction_when_full(self):
        """Test least recently used item is evicted when cache is full."""
        cache = TemplateCache(max_size=3)

        # Fill cache to capacity
        cache.put(Path("1.json"), {"id": 1})
        cache.put(Path("2.json"), {"id": 2})
        cache.put(Path("3.json"), {"id": 3})

        # Add one more (should evict oldest: 1.json)
        cache.put(Path("4.json"), {"id": 4})

        # 1.json should be evicted
        assert cache.get(Path("1.json")) is None
        # Others should still be present
        assert cache.get(Path("2.json")) == {"id": 2}
        assert cache.get(Path("3.json")) == {"id": 3}
        assert cache.get(Path("4.json")) == {"id": 4}

    def test_access_updates_recency(self):
        """Test accessing an item marks it as recently used."""
        cache = TemplateCache(max_size=3)

        # Fill cache
        cache.put(Path("1.json"), {"id": 1})
        cache.put(Path("2.json"), {"id": 2})
        cache.put(Path("3.json"), {"id": 3})

        # Access 1.json (makes it most recently used)
        cache.get(Path("1.json"))

        # Add new item (should evict 2.json, not 1.json)
        cache.put(Path("4.json"), {"id": 4})

        # 1.json should still be present (was accessed)
        assert cache.get(Path("1.json")) == {"id": 1}
        # 2.json should be evicted (least recently used)
        assert cache.get(Path("2.json")) is None
        # Others should be present
        assert cache.get(Path("3.json")) == {"id": 3}
        assert cache.get(Path("4.json")) == {"id": 4}

    def test_put_existing_key_updates_recency(self):
        """Test putting an existing key updates its recency."""
        cache = TemplateCache(max_size=3)

        # Fill cache
        cache.put(Path("1.json"), {"id": 1})
        cache.put(Path("2.json"), {"id": 2})
        cache.put(Path("3.json"), {"id": 3})

        # Update 1.json (makes it most recently used)
        cache.put(Path("1.json"), {"id": 1, "updated": True})

        # Add new item (should evict 2.json, not 1.json)
        cache.put(Path("4.json"), {"id": 4})

        # 1.json should still be present with updated value
        assert cache.get(Path("1.json")) == {"id": 1, "updated": True}
        # 2.json should be evicted
        assert cache.get(Path("2.json")) is None

    def test_single_item_cache(self):
        """Test cache with max_size=1."""
        cache = TemplateCache(max_size=1)

        cache.put(Path("1.json"), {"id": 1})
        assert cache.get(Path("1.json")) == {"id": 1}

        # Add second item (should evict first)
        cache.put(Path("2.json"), {"id": 2})
        assert cache.get(Path("1.json")) is None
        assert cache.get(Path("2.json")) == {"id": 2}


class TestInvalidation:
    """Test cache invalidation."""

    def test_invalidate_existing_key(self):
        """Test invalidating a key that exists."""
        cache = TemplateCache(max_size=10)
        key = Path("template.json")

        cache.put(key, {"genre": "Fantasy"})
        result = cache.invalidate(key)

        assert result is True
        assert cache.get(key) is None

    def test_invalidate_nonexistent_key(self):
        """Test invalidating a key that doesn't exist."""
        cache = TemplateCache(max_size=10)
        key = Path("notfound.json")

        result = cache.invalidate(key)

        assert result is False

    def test_invalidate_reduces_size(self):
        """Test invalidation reduces cache size."""
        cache = TemplateCache(max_size=10)

        cache.put(Path("1.json"), {"id": 1})
        cache.put(Path("2.json"), {"id": 2})

        assert cache.size == 2

        cache.invalidate(Path("1.json"))

        assert cache.size == 1


class TestClear:
    """Test cache clearing."""

    def test_clear_removes_all_entries(self):
        """Test clear removes all cached entries."""
        cache = TemplateCache(max_size=10)

        cache.put(Path("1.json"), {"id": 1})
        cache.put(Path("2.json"), {"id": 2})
        cache.put(Path("3.json"), {"id": 3})

        cache.clear()

        assert cache.size == 0
        assert cache.get(Path("1.json")) is None
        assert cache.get(Path("2.json")) is None
        assert cache.get(Path("3.json")) is None

    def test_clear_resets_statistics(self):
        """Test clear resets hit/miss counters."""
        cache = TemplateCache(max_size=10)

        cache.put(Path("1.json"), {"id": 1})
        cache.get(Path("1.json"))  # Hit
        cache.get(Path("2.json"))  # Miss

        stats_before = cache.get_stats()
        assert stats_before["hits"] > 0
        assert stats_before["misses"] > 0

        cache.clear()

        stats_after = cache.get_stats()
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0
        assert stats_after["hit_rate"] == 0.0

    def test_cache_works_after_clear(self):
        """Test cache works normally after being cleared."""
        cache = TemplateCache(max_size=10)

        cache.put(Path("1.json"), {"id": 1})
        cache.clear()

        # Should work normally
        cache.put(Path("2.json"), {"id": 2})
        assert cache.get(Path("2.json")) == {"id": 2}


class TestStatistics:
    """Test cache statistics and metrics."""

    def test_size_property(self):
        """Test size property returns correct count."""
        cache = TemplateCache(max_size=10)

        assert cache.size == 0

        cache.put(Path("1.json"), {"id": 1})
        assert cache.size == 1

        cache.put(Path("2.json"), {"id": 2})
        assert cache.size == 2

        cache.invalidate(Path("1.json"))
        assert cache.size == 1

    def test_hit_tracking(self):
        """Test cache hits are tracked correctly."""
        cache = TemplateCache(max_size=10)

        cache.put(Path("1.json"), {"id": 1})

        # First get is a hit
        cache.get(Path("1.json"))
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

        # Second get is also a hit
        cache.get(Path("1.json"))
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 0

    def test_miss_tracking(self):
        """Test cache misses are tracked correctly."""
        cache = TemplateCache(max_size=10)

        # Get on empty cache is a miss
        cache.get(Path("notfound.json"))
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

        # Another miss
        cache.get(Path("stillnotfound.json"))
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 2

    def test_hit_rate_calculation(self):
        """Test hit rate is calculated correctly."""
        cache = TemplateCache(max_size=10)

        cache.put(Path("1.json"), {"id": 1})

        # 1 hit, 0 misses = 100% hit rate
        cache.get(Path("1.json"))
        assert cache.hit_rate == 1.0

        # 1 hit, 1 miss = 50% hit rate
        cache.get(Path("notfound.json"))
        assert cache.hit_rate == 0.5

        # 2 hits, 1 miss = 66.67% hit rate
        cache.get(Path("1.json"))
        assert cache.hit_rate == pytest.approx(2 / 3)

    def test_hit_rate_empty_cache(self):
        """Test hit rate is 0 for empty cache with no accesses."""
        cache = TemplateCache(max_size=10)

        assert cache.hit_rate == 0.0

    def test_get_stats(self):
        """Test get_stats returns complete statistics."""
        cache = TemplateCache(max_size=5)

        cache.put(Path("1.json"), {"id": 1})
        cache.get(Path("1.json"))  # Hit
        cache.get(Path("2.json"))  # Miss

        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 5
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_max_size(self):
        """Test cache with max_size=0 (edge case)."""
        cache = TemplateCache(max_size=0)

        cache.put(Path("1.json"), {"id": 1})

        # Should evict immediately (size > 0)
        assert cache.size == 0
        assert cache.get(Path("1.json")) is None

    def test_large_max_size(self):
        """Test cache with very large max_size."""
        cache = TemplateCache(max_size=10000)

        # Add many items
        for i in range(100):
            cache.put(Path(f"{i}.json"), {"id": i})

        # All should be retained
        assert cache.size == 100
        for i in range(100):
            assert cache.get(Path(f"{i}.json")) == {"id": i}

    def test_path_objects_as_keys(self):
        """Test that Path objects work correctly as keys."""
        cache = TemplateCache(max_size=10)

        key1 = Path("template.json")
        key2 = Path("template.json")  # Same path, different object

        cache.put(key1, {"id": 1})

        # Should retrieve with different Path object
        assert cache.get(key2) == {"id": 1}

    def test_complex_values(self):
        """Test caching complex nested data structures."""
        cache = TemplateCache(max_size=10)
        key = Path("complex.json")

        complex_value = {
            "genre": "Fantasy",
            "sections": {
                "intro": ["line1", "line2"],
                "body": {"paragraphs": [1, 2, 3]},
            },
            "metadata": {"author": "Test", "version": 1.0},
        }

        cache.put(key, complex_value)
        result = cache.get(key)

        assert result == complex_value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
