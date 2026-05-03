from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
from threading import Lock
from time import monotonic


@dataclass(slots=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: float


@dataclass(slots=True)
class TokenBucket:
    capacity: int
    refill_per_second: float
    tokens: float
    last_refill_at: float

    def refill(self, now: float) -> None:
        elapsed = now - self.last_refill_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last_refill_at = now


class DistributedRateLimiter:
    def __init__(self, shard_count: int = 4) -> None:
        self._shards = [dict() for _ in range(shard_count)]
        self._locks = [Lock() for _ in range(shard_count)]

    def _select_shard(self, key: str) -> tuple[dict[str, TokenBucket], Lock]:
        digest = md5(key.encode("utf-8"), usedforsecurity=False).hexdigest()
        index = int(digest, 16) % len(self._shards)
        return self._shards[index], self._locks[index]

    def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision:
        now = monotonic()
        refill_per_second = limit / window_seconds
        shard, lock = self._select_shard(key)

        with lock:
            bucket = shard.get(key)
            if bucket is None:
                bucket = TokenBucket(
                    capacity=limit,
                    refill_per_second=refill_per_second,
                    tokens=float(limit),
                    last_refill_at=now,
                )
                shard[key] = bucket

            bucket.refill(now)
            if bucket.tokens >= 1:
                bucket.tokens -= 1
                return RateLimitDecision(
                    allowed=True,
                    remaining=int(bucket.tokens),
                    retry_after_seconds=0.0,
                )

            missing_tokens = 1 - bucket.tokens
            retry_after_seconds = missing_tokens / bucket.refill_per_second
            return RateLimitDecision(
                allowed=False,
                remaining=0,
                retry_after_seconds=retry_after_seconds,
            )


def main() -> None:
    limiter = DistributedRateLimiter(shard_count=3)
    for attempt in range(1, 7):
        decision = limiter.check("user:123", limit=5, window_seconds=60)
        print(f"attempt={attempt} decision={decision}")


if __name__ == "__main__":
    main()