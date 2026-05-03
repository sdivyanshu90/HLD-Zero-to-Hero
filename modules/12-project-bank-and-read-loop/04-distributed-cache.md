# Cheat Sheet: Distributed Cache

## Scale (BoE)
```
Target: 1M QPS cache reads, 50K QPS cache writes
Cache size: 100 GB working set
Hit rate target: 95%+
Latency: < 1ms P99
```

## System Diagram
```
Client ──GET key──▶ Client lib (consistent hashing) ──▶ Redis Node 1
                                                    ──▶ Redis Node 2
                                                    ──▶ Redis Node 3
                                                          │ cache miss
                                                    ──▶ Database
                                                    (repopulate cache)
```

## Key Design Decisions

**1. Distribution strategy:**
- Consistent hashing: add/remove node → moves only 1/N of keys
- Virtual nodes (150 per physical): even distribution even with different capacity nodes
- Redis Cluster: 16,384 hash slots, built-in consistent hashing

**2. Eviction policy:**
- LRU (allkeys-lru): evict least recently used → good for most web apps
- LFU (allkeys-lfu): evict least frequently used → better for viral content
- Default: volatile-lru (only evict keys with TTL set)

**3. Cache-aside vs write-through:**
- Cache-aside (most common): app reads cache, miss → load from DB, populate cache
- Write-through: write to cache AND DB synchronously (consistent, slower writes)

**4. Thundering herd:**
- TTL jitter: expire = base_ttl + random(0, base_ttl * 0.1)
- Mutex: one request recomputes, others wait on lock key

## Bottlenecks
1. Hot key: one key receives disproportionate traffic → replicate key N times
2. Memory pressure: monitor `used_memory` vs `maxmemory` → add nodes when >80%

## Unique Trick
Redis is single-threaded for commands, so all operations are atomic without locks. Use `SET key value NX EX 5` for distributed locks. Use sorted sets (ZADD/ZRANGEBYSCORE) for leaderboards, rate limiting windows, and time-series data in Redis.
