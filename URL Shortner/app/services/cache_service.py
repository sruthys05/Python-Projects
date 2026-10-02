from dataclasses import dataclass
from datetime import datetime

from app.config import settings
from app.dsa.lru_cache import LRUCache


@dataclass(frozen=True)
class CachedURL:
    long_url: str
    expires_at: datetime


class URLCache:
    def __init__(self, capacity: int = settings.cache_size) -> None:
        self._cache: LRUCache[str, CachedURL] = LRUCache(capacity)

    def get(self, short_code: str) -> CachedURL | None:
        return self._cache.get(short_code)

    def put(self, short_code: str, long_url: str, expires_at: datetime) -> None:
        self._cache.put(short_code, CachedURL(long_url, expires_at))

    def invalidate(self, short_code: str) -> None:
        self._cache.pop(short_code)

    def clear(self) -> None:
        self._cache.clear()
