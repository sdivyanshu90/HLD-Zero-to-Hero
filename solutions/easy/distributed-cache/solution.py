from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import md5
from typing import Any, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class CacheItem:
    value: Any
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        return self.expires_at is not None and utcnow() >= self.expires_at


class LRUCacheShard:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._items: OrderedDict[str, CacheItem] = OrderedDict()

    def get(self, key: str) -> Any | None:
        item = self._items.get(key)
        if item is None:
            return None
        if item.is_expired():
            self._items.pop(key, None)
            return None

        self._items.move_to_end(key)
        return item.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = None
        if ttl_seconds is not None:
            expires_at = utcnow() + timedelta(seconds=ttl_seconds)

        self._items[key] = CacheItem(value=value, expires_at=expires_at)
        self._items.move_to_end(key)
        self._evict_if_needed()

    def delete(self, key: str) -> None:
        self._items.pop(key, None)

    def _evict_if_needed(self) -> None:
        while len(self._items) > self.capacity:
            self._items.popitem(last=False)

    def debug_keys(self) -> list[str]:
        return list(self._items.keys())


class ShardedDistributedCache:
    def __init__(self, shard_count: int, capacity_per_shard: int) -> None:
        if shard_count <= 0:
            raise ValueError("shard_count must be positive")
        self._shards = [LRUCacheShard(capacity=capacity_per_shard) for _ in range(shard_count)]

    def _select_shard(self, key: str) -> LRUCacheShard:
        digest = md5(key.encode("utf-8"), usedforsecurity=False).hexdigest()
        shard_index = int(digest, 16) % len(self._shards)
        return self._shards[shard_index]

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        self._select_shard(key).set(key, value, ttl_seconds)

    def get(self, key: str) -> Any | None:
        return self._select_shard(key).get(key)

    def delete(self, key: str) -> None:
        self._select_shard(key).delete(key)

    def debug_layout(self) -> dict[int, list[str]]:
        return {index: shard.debug_keys() for index, shard in enumerate(self._shards)}


def main() -> None:
    cache = ShardedDistributedCache(shard_count=3, capacity_per_shard=2)

    cache.set("session:1", {"user": "alice"}, ttl_seconds=30)
    cache.set("session:2", {"user": "bob"}, ttl_seconds=30)
    cache.set("session:3", {"user": "carol"}, ttl_seconds=30)
    cache.set("session:4", {"user": "dave"}, ttl_seconds=30)

    print("Current shard layout:")
    print(cache.debug_layout())
    print()
    print("Fetch one key:")
    print(cache.get("session:3"))


if __name__ == "__main__":
    main()