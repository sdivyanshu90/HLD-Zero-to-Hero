# Step 7 — Clock Drift and Consistency

## Window Boundary Problem

```
Server A clock: 10:00:59.999
Server B clock: 10:01:00.001  ← 2ms ahead

Request hits Server A: assigned to window 10:00 (expires at 10:01)
Request hits Server B: assigned to window 10:01 (new fresh window)

Both windows counted separately → user gets ~2× limit at boundary
```

## Mitigation: Use Redis Server Clock

```lua
-- Always use Redis TIME command (not client clock)
local now = redis.call('TIME')  -- returns {seconds, microseconds}
local now_ms = now[1] * 1000 + math.floor(now[2] / 1000)
local window_id = math.floor(now_ms / 60000)  -- per-minute window
```

Redis TIME is monotonic within a single server instance.

## Multi-Region Consistency

```
Region A (US-East): has its own Redis cluster
Region B (EU-West): has its own Redis cluster

Per-region limits: 100 req/min × 2 regions = 200 total
  → User can exceed intended global limit

Solutions:
  1. Region-local limits (accept 2× global as trade-off)
  2. Global Redis (cross-region latency ~50-100ms, too slow)
  3. CRDT counters: PN-Counter with gossip sync (eventual, ~1s lag)
     Riak CRDT, Redis CRFT module
  4. Approximate: each region enforces global_limit / region_count
     Re-balance when traffic shifts
```

## Accuracy vs Performance Trade-Off

| Approach | Accuracy | Latency | Complexity |
|----------|----------|---------|------------|
| Centralised Redis + Lua | High (soft limit) | 2-5 ms | Low |
| Per-server local counter | Low (× N servers) | < 0.1 ms | Low |
| Local + periodic sync | Medium | < 1 ms | Medium |
| CRDT gossip | Medium (eventual) | < 0.5 ms | High |
| Sliding window log | Exact | 5-10 ms | Medium |
