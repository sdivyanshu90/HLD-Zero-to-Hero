from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from urllib.parse import urlparse


BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def encode_base62(number: int) -> str:
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return BASE62_ALPHABET[0]

    value = number
    encoded: list[str] = []
    while value:
        value, remainder = divmod(value, 62)
        encoded.append(BASE62_ALPHABET[remainder])
    return "".join(reversed(encoded))


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


@dataclass(slots=True)
class ShortURLRecord:
    short_code: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return False
        current_time = now or utcnow()
        return current_time >= self.expires_at


class TTLCache:
    def __init__(self) -> None:
        self._items: Dict[str, tuple[ShortURLRecord, Optional[datetime]]] = {}

    def get(self, key: str) -> Optional[ShortURLRecord]:
        cached = self._items.get(key)
        if cached is None:
            return None

        record, expires_at = cached
        if expires_at is not None and utcnow() >= expires_at:
            self._items.pop(key, None)
            return None
        return record

    def set(self, key: str, value: ShortURLRecord, ttl_seconds: Optional[int]) -> None:
        expires_at = None
        if ttl_seconds is not None:
            expires_at = utcnow() + timedelta(seconds=ttl_seconds)
        self._items[key] = (value, expires_at)


class InMemoryURLStore:
    def __init__(self) -> None:
        self._records: Dict[str, ShortURLRecord] = {}
        self._next_id = 1

    def next_identifier(self) -> int:
        identifier = self._next_id
        self._next_id += 1
        return identifier

    def save(self, record: ShortURLRecord) -> None:
        self._records[record.short_code] = record

    def get(self, short_code: str) -> Optional[ShortURLRecord]:
        return self._records.get(short_code)

    def exists(self, short_code: str) -> bool:
        return short_code in self._records


class URLShortenerService:
    def __init__(self, base_url: str, cache_ttl_seconds: int = 300) -> None:
        self._base_url = base_url.rstrip("/")
        self._store = InMemoryURLStore()
        self._cache = TTLCache()
        self._cache_ttl_seconds = cache_ttl_seconds

    def create_short_url(
        self,
        long_url: str,
        *,
        custom_alias: Optional[str] = None,
        expires_in_seconds: Optional[int] = None,
    ) -> str:
        if not is_valid_url(long_url):
            raise ValueError("long_url must be an absolute URL")

        short_code = custom_alias or encode_base62(self._store.next_identifier())
        if self._store.exists(short_code):
            raise ValueError(f"short code '{short_code}' already exists")

        expires_at = None
        if expires_in_seconds is not None:
            expires_at = utcnow() + timedelta(seconds=expires_in_seconds)

        record = ShortURLRecord(
            short_code=short_code,
            long_url=long_url,
            created_at=utcnow(),
            expires_at=expires_at,
        )
        self._store.save(record)
        self._cache.set(short_code, record, self._cache_ttl_seconds)
        return f"{self._base_url}/{short_code}"

    def resolve(self, short_code: str) -> Optional[str]:
        record = self._cache.get(short_code)
        if record is None:
            record = self._store.get(short_code)
            if record is None:
                return None
            self._cache.set(short_code, record, self._cache_ttl_seconds)

        if record.is_expired():
            return None
        return record.long_url


def main() -> None:
    service = URLShortenerService(base_url="https://sho.rt")

    article = service.create_short_url(
        "https://example.com/articles/system-design",
        expires_in_seconds=3600,
    )
    docs = service.create_short_url(
        "https://docs.example.com/reference/redis",
        custom_alias="redis-guide",
    )

    print("Created short URLs:")
    print(article)
    print(docs)
    print()
    print("Resolved target:")
    print(service.resolve("redis-guide"))


if __name__ == "__main__":
    main()