# Step 2 — Traffic Model and Capacity

## Scale Assumptions

```
Total API traffic:      100 K req/sec
Rate limit checks:      1 per request = 100 K checks/sec
Redis operations:       ~2 per check (GET + INCR, or Lua script)
Redis ops/sec needed:   200 K ops/sec
Redis throughput:       100 K+ ops/sec per node (pipelining)
→ 2-3 Redis nodes adequate with replication
```

## Memory Estimation

```
Per counter entry:
  key:   ~50 B (e.g., "rl:user:12345:min:2024-05-03T10:30")
  value: 8 B (int64 counter)
  TTL:   stored in Redis expiry table
  Total: ~100 B overhead

Distinct active users: 1 M concurrent
Counters per user:     3 (second + minute + hour)
Total entries:         3 M
Memory:                3 M × 100 B = 300 MB  ← fits in single Redis
```

## Response Headers to Return

```
HTTP/1.1 200 OK
X-RateLimit-Limit:     1000
X-RateLimit-Remaining: 745
X-RateLimit-Reset:     1714694460   (Unix epoch of window reset)

HTTP/1.1 429 Too Many Requests
Retry-After:           37           (seconds until next window)
X-RateLimit-Limit:     1000
X-RateLimit-Remaining: 0
```
