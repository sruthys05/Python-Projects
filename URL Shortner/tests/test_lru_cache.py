import pytest

from app.dsa.lru_cache import LRUCache


def test_get_updates_recency_and_eviction_removes_least_recent() -> None:
    cache = LRUCache[str, int](2)
    cache.put("first", 1)
    cache.put("second", 2)

    assert cache.get("first") == 1
    cache.put("third", 3)

    assert cache.get("first") == 1
    assert cache.get("second") is None
    assert cache.get("third") == 3
    assert len(cache) == 2


def test_put_updates_existing_value_without_growing_cache() -> None:
    cache = LRUCache[str, int](1)
    cache.put("key", 1)
    cache.put("key", 2)

    assert cache.get("key") == 2
    assert len(cache) == 1


def test_pop_and_clear() -> None:
    cache = LRUCache[str, int](2)
    cache.put("key", 1)

    assert cache.pop("key") == 1
    assert cache.pop("missing") is None
    cache.put("other", 2)
    cache.clear()
    assert len(cache) == 0


def test_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        LRUCache[str, int](0)
