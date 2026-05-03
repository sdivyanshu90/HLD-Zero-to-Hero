# Cache Failure Modes

## The Three Classic Failures

Cache failures can cascade into database overload and system-wide outages:

```
Three failure modes:
  1. Cache Stampede (Thundering Herd): many requests miss cache simultaneously
  2. Cache Avalanche: large portion of cache expires simultaneously
  3. Cache Penetration: requests for non-existent keys bypass cache entirely
```

---

## Cache Stampede (Thundering Herd)

Covered in detail in [03-write-policies.md]. Summary:

```
Cause: popular cache entry expires → many requests simultaneously miss
  → All hit database → DB overwhelmed

Fixes:
  ✓ Mutex lock on cache miss (only 1 recomputes, others wait)
  ✓ TTL jitter (randomize expiry times to avoid simultaneous expiry)
  ✓ Background refresh (preemptively refresh before expiry)
  ✓ Redundant keys: keep "stale" key with longer TTL as fallback
      main key TTL: 60s, stale key TTL: 3600s
      If main key miss: background refresh + serve stale key immediately
```

---

## Cache Avalanche

A large fraction of the cache becomes unavailable simultaneously:

```
Scenario 1: Large batch of entries set with the same TTL
  5 million entries set with TTL=3600s at system startup
  After 1 hour: ALL 5 million expire simultaneously
  → 5 million cache misses in seconds → DB overwhelmed

  Fix: Jitter on TTL
    TTL = 3600 + random(-300, 300)  # ±5 minutes of variance
    → Expires are staggered over 10-minute window instead of instantaneous

Scenario 2: Cache service itself fails (Redis crash, OOM)
  All cache nodes become unavailable simultaneously
  → Every request hits database
  → DB was sized for 5% cache miss rate → instant overload

  Fix: Circuit breaker
    On cache service failure: trip circuit breaker
    Requests bypass cache and go direct to DB (until DB starts degrading)
    Apply rate limiting / shed load to protect DB
    Restart/failover cache service
  
  Fix: Redis Cluster
    Distribute cache across multiple nodes
    Single node failure loses only 1/N of cache (e.g., 1/6 for 6 nodes)
    → 16% cache miss increase, not 100%
    
  Fix: Multi-layer cache
    L1: in-process cache (not affected by Redis failure)
    L2: Redis (may be unavailable)
    L3: DB (fallback)
    → In-process cache insulates against Redis outage for recent data
```

---

## Cache Penetration

Requests for keys that **don't exist** in the database keep hitting the DB because the cache also never has them:

```
Normal cache behavior:
  Request for user:1234 (exists) → cache miss → DB → cache.set(user:1234, data)
  Next request for user:1234 → cache hit ✓

Cache penetration:
  Request for user:99999999 (does NOT exist in DB)
  → cache miss
  → DB query (returns empty)
  → Nothing to cache (cannot cache "not found"!)
  → Next 1,000 requests for user:99999999: ALL hit DB every time!

Attack scenario:
  Attacker discovers URL pattern: /api/user/{id}
  Sends 10M requests with random IDs that don't exist
  → DB gets 10M queries for non-existent users
  → DB overloaded → real users can't access their data
```

### Fixes for Cache Penetration

```
Fix 1: Cache negative results (null caching)
  If DB returns empty → cache.set(f"user:99999999", NULL, ttl=60)
  Next request: cache hit → return empty immediately
  
  Risk: if user is created shortly after: stale "not found" for 60 seconds
  Mitigation: short TTL for null entries (60s vs 3600s for real entries)
  
  Risk: large attack with many different fake IDs fills cache with null entries
  Mitigation: use a very short TTL (5s) and limit cache size

Fix 2: Bloom filter at API gateway
  Pre-load bloom filter with all valid user IDs
  Request for user:99999999 → bloom filter says "definitely NOT in DB" → return 404 immediately
  No DB query, no cache query
  
  Update: when new user is created → add to bloom filter
  (bloom filters only support add, not delete; use rotating bloom filters for deletes)
  
  Memory: 10 bits per user × 1B users = 10Gb / 8 = 1.25 GB → feasible

Fix 3: Rate limiting / API gateway protection
  Limit requests per IP to N/second
  Detect and block suspicious patterns (1 IP, 10,000 different non-existent IDs)
```

---

## Cache Hotspot (Hot Key)

One cache key receives disproportionate traffic:

```
Scenario: Celebrity user has 10M followers. Their profile is fetched with every feed refresh.
  profile:celebrity_user → cache key
  Receives 100K reads/second
  Single Redis node serving this key: overloaded!
  (Redis single thread, single key = single node bottleneck)

Fixes:
  1. Local in-process caching: 
     Each app server has its own copy in process memory
     → 100 app servers, each has 1 copy → 100× read distribution
     → But updates must invalidate all 100 copies
  
  2. Key replication (hot key sharding):
     store profile:celebrity_user as N copies:
       profile:celebrity_user:0, profile:celebrity_user:1, ..., :N-1
     Each assigned to a different Redis node
     Read: cache.get(f"profile:celebrity_user:{random(0,N-1)}")
     Write: update ALL N copies (fan-out write)
     
     Cost: N× memory + N write operations per update
     Benefit: N× read throughput, perfectly distributed
  
  3. Read replicas for Redis:
     Redis primary for writes + N Redis replicas for reads
     Route reads round-robin across replicas
     (Redis Cluster doesn't auto-rebalance read load; requires client-side logic)
```

---

## Consistency Patterns

```
Strong consistency (read-after-write):
  After a write, any subsequent read returns the new value
  Implementation: 
    Write to DB → invalidate cache → next read reloads from DB
    All subsequent reads see new value
  Risk: "lost update" race:
    t=0: write DB (user balance = 100)
    t=1: invalidate cache
    t=2: another thread reads (cache miss, reloads balance=100 from DB)
    t=3: write again (user balance = 110)
    t=4: invalidate cache
    t=5: cache now empty, next read loads 110 ← CORRECT
    
    But if t=2 happens AFTER t=3, old value (100) is cached → wrong!
    Fix: update cache atomically only if DB value matches expected version

Eventual consistency (acceptable stale reads):
  Writes go to DB; cache has TTL; after TTL expires, cache reloads
  Reads between write and TTL expiry may see old value
  
  Acceptable for: social media feeds, profile views, product descriptions
  Not for: banking, inventory, authentication tokens
```

---

## Interview Quick Answers

- **What is cache penetration and how do you fix it?** — Cache penetration: requests for keys that don't exist in the DB keep causing DB queries (cache can't cache "not found"). Fix: cache null results with short TTL, or use a bloom filter to reject queries for definitely-absent keys before they reach the cache or DB.
- **What is cache avalanche?** — A large portion of cache becomes unavailable simultaneously (either many entries expire at once, or the cache service crashes). Fix: TTL jitter (staggered expiry), Redis Cluster (single node failure loses only 1/N of cache), and circuit breakers to protect DB when cache is down.
- **How do you cache a hot key in Redis?** — Create N copies of the key with random suffixes, each mapped to a different Redis node. Reads pick a random copy. Writes update all N copies. This distributes the read load across N nodes at the cost of N× memory and write fan-out.
