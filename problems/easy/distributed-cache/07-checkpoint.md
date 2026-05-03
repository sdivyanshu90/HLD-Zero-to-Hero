# Step 7 — Checkpoint & Interview Q&A

**Q1: Why consistent hashing instead of modulo hashing for distributing keys?**
> Modulo hashing remaps nearly all keys when the number of nodes changes, causing a thundering herd of cache misses. Consistent hashing remaps only 1/N of keys on node addition/removal, minimising disruption.

**Q2: How does LRU achieve O(1) GET and SET?**
> HashMap provides O(1) key-to-node lookup. Doubly-linked list provides O(1) move-to-front (given a node pointer) and O(1) tail removal. The combination gives O(1) both operations.

**Q3: What happens when a cache node goes down?**
> The consistent hash ring detects the node as unavailable. Keys map to the next node clockwise. If replication is enabled, the replica serves reads. Without replication, cache miss → DB fallback. This may cause a brief thundering herd mitigated by request coalescing or circuit breakers.

**Q4: Redis vs Memcached — when would you choose each?**
> Redis: rich data structures (sorted sets, streams, pub/sub), persistence, Lua scripting, cluster mode with replication. Memcached: pure simplicity, multi-threaded (better CPU utilisation for single large caches), no persistence needed. Choose Memcached only when you need raw throughput on a single flat key-value workload and care nothing for persistence.

**Q5: How do you handle a cold cache after a restart?**
> 1. Redis RDB/AOF persistence pre-warms cache. 2. Cache-aside pattern: first request misses, warms cache. 3. Scheduled warm-up script: pre-populate top N hot keys from DB at startup. 4. Request coalescing: only one request fetches from DB, others wait.

## Trade-Off Summary

```
Persistence  ON  → safer, slower writes (AOF fsync)
Persistence  OFF → faster, cold restart problem

Replication  ON  → HA, 2× memory cost
Replication  OFF → cheaper, single point of failure

Virtual nodes HIGH → uniform distribution, more ring metadata
Virtual nodes LOW  → cheaper, possible hot spots
```
