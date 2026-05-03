# Module 08 Checkpoint: Caching Strategies

## Questions

---

**Q1.** Your web app has 1,000 QPS on a user profile endpoint. DB query takes 50ms. How would you cache this?

> **Answer:**
> 1. **Redis cache-aside**: `GET user:{id}` → if miss, query DB, `SET user:{id} {data} EX 300` (5min TTL)
> 2. Expected behavior: after first miss, next 300 seconds of requests hit cache (~0.5ms, not 50ms)
> 3. On profile update: `DEL user:{id}` to invalidate; next read reloads from DB
> 4. With 300s TTL and 1000 QPS: 3-4 misses/minute (1 per TTL expiry) → DB sees ~0.007% of traffic
> 5. Consider: TTL jitter (random 240-360s) to avoid simultaneous expiry, in-process L1 cache for ultra-hot profiles

---

**Q2.** Why can't you use a standard Redis Bloom filter to handle deletions (e.g., when a user is deleted)?

> **Answer:** Standard Bloom filters only support insert and query. When a user is deleted, you cannot remove them from the bloom filter (their bits may be shared with other users). Solutions: (1) **Counting Bloom filter** (count per bit, decrement on remove, 2-4× memory) (2) **Rotating Bloom filter** (two alternating filters; periodically reset the older one and rebuild) (3) Use a separate "tombstone" set of deleted IDs checked before the bloom filter.

---

**Q3.** Compare write-through vs write-behind for a social media "like" counter.

> **Answer:**
> - **Write-through**: every like → update both Redis cache AND DB. 1000 likes/second → 1000 DB writes/second. DB under heavy load, writes blocked by DB latency.
> - **Write-behind**: every like → update Redis cache immediately (fast!) → batch-write to DB every 100ms. 1000 likes/second → 10 DB writes/100ms batch = 10 DB round trips/second. Much lower DB load.
> - **Choice**: write-behind for like counters. Losing a few likes during a cache failure is acceptable. Financial data would require write-through or direct DB writes.

---

**Q4.** A Redis node in your cluster has died. What is the impact and how do you mitigate it?

> **Answer:** With Redis Cluster (N nodes): the failed node's key slots are unavailable. Impact depends on cluster setup:
> - If primary failed with no replica: those slots are down (read/write errors)
> - With replicas: promotion happens automatically (~10-30s)
> - During failover: cache miss rate spikes for that node's keys → DB load increases
>
> Mitigation: always run Redis Cluster with at least 1 replica per primary. Add multi-layer caching (in-process L1 cache insulates against Redis failures for recently accessed data). Implement circuit breaker: if Redis failure rate > threshold, gracefully degrade to direct DB reads with DB-level rate limiting.

---

**Q5.** What is the difference between TTL-based expiry and LRU eviction?

> **Answer:**
> - **TTL expiry**: entries expire after a time duration regardless of access frequency. Ensures data freshness (stale data eventually disappears). Use for time-sensitive data (session tokens, auth state, mutable product prices).
> - **LRU eviction**: entries are evicted when cache is full, removing the least recently accessed. Size-based memory management. Does NOT guarantee data freshness.
> - Use BOTH together in production: TTL for correctness (no permanently stale data), LRU/capacity limit for memory management.

---

## Checklist

- [ ] Cache tiers: CPU/OS → in-process → Redis → CDN
- [ ] Redis vs Memcached: data structures, persistence, clustering
- [ ] Eviction policies: LRU (temporal locality), LFU (frequency), ARC (adaptive), TinyLFU (modern)
- [ ] Write policies: write-through (consistent), write-behind (fast writes), cache-aside (simple)
- [ ] Thundering herd: mutex, TTL jitter, background refresh
- [ ] Cache avalanche: jitter, Redis Cluster, circuit breaker
- [ ] Cache penetration: null caching, bloom filter, rate limiting
- [ ] Hot key problem: in-process caching, key replication/sharding
- [ ] Consistency: invalidate on write (strong), TTL-based (eventual)
