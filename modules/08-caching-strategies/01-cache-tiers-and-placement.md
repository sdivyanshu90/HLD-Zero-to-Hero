# Cache Tiers and Placement

## Why Cache?

The memory hierarchy creates a 1,000-10,000× performance difference between RAM and disk:

```
Latency:
  L1 cache (CPU):     1 ns
  L2 cache (CPU):     4 ns
  L3 cache (CPU):    40 ns
  RAM:               80 ns    ← application-level caching lives here
  NVMe SSD:         100 µs   ← 1,000× slower than RAM
  Network (same DC):   500 µs ← distributed cache (Redis)
  Network DB read:    1-5 ms  ← database query

Goal: serve requests from the fastest tier possible
Goal: keep as much "hot" data in RAM as possible
```

---

## Cache Tier 1: CPU and OS Page Cache

```
Automatic, managed by hardware and OS:
  CPU L1/L2/L3: hardware-managed, code and data hot spots
  OS page cache: every file read is buffered in kernel memory
  
  Database buffer pool IS the page cache for the DB:
    PostgreSQL: shared_buffers (typically 25% of RAM)
    MySQL: innodb_buffer_pool_size (typically 70-80% of RAM)
  
  First "free" cache: most applications benefit from this without
  any extra effort. Ensure database server has enough RAM for its
  working set to fit in the buffer pool.
```

---

## Cache Tier 2: Application-Level Local Cache (In-Process)

```
Cache lives inside the application process (same JVM/Python process):

  ┌─────────────────────────────────────────────────────┐
  │  Application Process                                 │
  │                                                      │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  In-process LRU cache (Guava, Caffeine)       │   │
  │  │  user:1234 → {name: "Alice", role: "admin"}   │   │
  │  │  product:567 → {name: "Phone", price: 999}    │   │
  │  │  (max 10,000 entries, TTL=60s)                 │   │
  │  └──────────────────────────────────────────────┘   │
  │                │ miss                                 │
  │                ▼                                     │
  │  ┌────────────────┐                                  │
  │  │   Downstream   │                                  │
  │  │   (DB, API)    │                                  │
  │  └────────────────┘                                  │
  └─────────────────────────────────────────────────────┘

Advantages:
  ✓ Zero network latency (in same process, in RAM)
  ✓ No serialization/deserialization overhead
  ✓ Sub-microsecond access time

Disadvantages:
  ✗ Not shared across application instances
  ✗ Memory pressure (competes with application heap)
  ✗ Cache invalidation: updating cache in one process doesn't update others
  ✗ Cache lost on process restart

Best for: reference data (rarely changing), per-process TTL-based caching
Examples: Caffeine (Java), functools.lru_cache (Python), Node.js in-memory Map
```

---

## Cache Tier 3: Distributed Cache (Remote)

```
Shared cache service accessed over the network:

  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ App      │  │ App      │  │ App      │
  │ Server 1 │  │ Server 2 │  │ Server 3 │
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │              │              │
       └──────────────┼──────────────┘
                      │ TCP
                      ▼
            ┌──────────────────┐
            │   Redis Cluster   │
            │  (shared cache)   │
            └──────────────────┘
                      │ miss
                      ▼
            ┌──────────────────┐
            │    Database       │
            └──────────────────┘

Advantages:
  ✓ Shared across ALL application instances
  ✓ Cache survives app restart (Redis persistence optional)
  ✓ Much larger capacity (GB to TB across cluster)
  ✓ Atomic operations (INCR, SET NX) for distributed algorithms

Disadvantages:
  ✗ Network latency (~0.5ms same-DC)
  ✗ Serialization/deserialization overhead
  ✗ Another infrastructure component to operate

Examples: Redis, Memcached, Hazelcast, Apache Ignite
```

---

## Cache Tier 4: CDN (Edge Cache)

```
Cache at Points of Presence (PoPs) globally:

  User in NYC ──▶ CDN PoP NYC (cache hit!) ──▶ fast response
  User in NYC ──▶ CDN PoP NYC (cache miss) ──▶ Origin Server
  
  Content cached at edge for: static assets, images, videos, API responses

  Cache-Control headers control CDN caching:
    Cache-Control: public, max-age=86400
    → CDN caches for 24 hours, serves without hitting origin
    
    Cache-Control: private, no-store
    → CDN does NOT cache (user-specific content, financial data)

Examples: Cloudflare, AWS CloudFront, Fastly, Akamai
Best for: static assets (JS/CSS/images), large files (video), 
          public API responses with high repetition
```

---

## Multi-Tier Cache Architecture

```
Full request flow:

  Client ──▶ CDN Edge ──(miss)──▶ API Server
                                      │
                                  In-process cache
                                      │ (miss)
                                  Redis cluster
                                      │ (miss)
                                  Database
  
  Hit rates (typical production):
    CDN: 80-95% (for static content / public APIs)
    In-process: 40-70% (hot reference data)
    Redis: 85-99% (shared application cache)
    Database: handles < 1-15% of all requests
```

---

## Redis vs Memcached

```
Feature           Redis                    Memcached
──────────────────────────────────────────────────────────
Data structures   Strings, Hash, List,     String only (K-V)
                  Set, ZSet, Streams, etc.
Persistence       RDB + AOF (optional)     None (pure cache)
Replication       Primary-replica          None (manual)
Clustering        Redis Cluster (sharding) Client-side sharding
Transactions      MULTI/EXEC               None
Lua scripting     Yes (atomic operations)  No
Pub/Sub           Yes                      No
Memory limit      Configurable (eviction)  Configurable (eviction)
Performance       ~100K ops/s per node     ~1M ops/s per node
Use case          Feature-rich, durable    Ultra-fast pure cache

Choose Redis when:
  - Need persistence (cache survives restart)
  - Need complex data structures (sorted sets for leaderboards)
  - Need pub/sub (real-time notifications, fan-out)
  - Need atomic operations (rate limiting, distributed locks)
  - Need Lua scripts for complex atomic operations

Choose Memcached when:
  - Pure caching, no persistence needed
  - Multi-threaded performance critical
  - Simple key-value only
  - Already using a Memcached-compatible library
```

---

## Interview Quick Answers

- **Why use an in-process cache AND Redis?** — In-process is ~0µs (no network), Redis is ~500µs (network). Layer them: check in-process first (for ultra-hot data), then Redis, then DB. In-process has low capacity and not shared; Redis has large shared capacity. Together: sub-microsecond hits for hottest data, millisecond hits for warm data.
- **When should you NOT cache a value?** — When the value is user-specific and private (password hash, banking balance), when it changes so frequently that the cache is nearly always stale (real-time stock prices), when the cost of a stale read is unacceptable (inventory count), or when the key space is so large that hit rate is near zero.
