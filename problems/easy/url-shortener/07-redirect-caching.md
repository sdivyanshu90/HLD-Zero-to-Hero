# Step 7 — Redirect Caching

## Cache Architecture

```
Client
  │
  ▼ DNS resolves to nearest PoP
┌──────────────────┐
│   CDN Edge PoP   │  Cache-Control: max-age (for 301)
└────────┬─────────┘
         │ miss
         ▼
┌──────────────────┐
│  Redis Cluster   │  Key: short_code → long_url + metadata
│  (in-memory)     │  TTL: 24 hours (refreshed on hit)
└────────┬─────────┘
         │ miss
         ▼
┌──────────────────┐
│  MySQL Replica   │  SELECT long_url, expires_at FROM short_urls
└──────────────────┘
```

## 301 vs 302 Trade-Off

| Aspect | 301 Permanent | 302 Temporary |
|--------|---------------|---------------|
| Browser caches? | Yes (indefinitely) | No |
| Server sees every hit? | No (after first) | Yes |
| Analytics tracking | ✗ (misses repeats) | ✓ |
| Server load | Lower | Higher |
| Click counting accuracy | ✗ | ✓ |

**Decision:** Use 302 if analytics matter. Use 301 for performance-first (Bitly uses 301 for speed, 302 for tracking links).

## Cache Eviction Policy

```
Policy: allkeys-lru (evict least recently used when memory full)
TTL per entry: 24 hours (sliding; reset on every access)
Redis memory: 6 GB for hot set (see BoE)
```

## Thundering Herd on Cache Miss

When a popular URL expires simultaneously:
```
Mitigation 1: TTL jitter
  TTL = base_ttl + random(0, base_ttl * 0.1)

Mitigation 2: Redis lock (mutex)
  SET lock:{code} 1 NX PX 200
  if acquired: fetch DB, populate cache, release lock
  else: spin-wait 10ms and retry (or return stale)

Mitigation 3: Background refresh
  When TTL < 10%, async refresh before it expires
```

## Cache Penetration (non-existent codes)

Attackers flood with random codes → all miss → DB overwhelmed.
```
Solution:
  1. Cache negative results: Redis SET short_code "" TTL 60s
  2. Bloom filter in Redirect Service: if not in bloom → 404 immediately
```
