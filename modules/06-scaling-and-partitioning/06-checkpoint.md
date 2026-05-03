# Module 06 Checkpoint: Scaling and Partitioning

## Questions to Test Your Understanding

---

**Q1.** A startup's PostgreSQL database is getting slow. What are the steps you'd take before sharding?

> **Answer:**
> 1. **Query optimization**: add missing indexes, rewrite N+1 queries, use EXPLAIN ANALYZE to find slow queries
> 2. **Connection pooling**: add PgBouncer (reduces connection overhead from thousands of short-lived connections)
> 3. **Caching**: add Redis in front of the DB for hot reads (deflect 80-95% of reads)
> 4. **Read replicas**: add 1-3 async read replicas, route read traffic there (scale reads 4-10×)
> 5. **Vertical scaling**: upgrade to a larger instance (more RAM = larger buffer pool = more cache hits)
> 6. **Table partitioning** (pg_partman): partition large tables by range (e.g., monthly partitions for time-series) — does NOT add distributed systems complexity
> 7. Only after all of the above: horizontal sharding

---

**Q2.** You're using hash-based sharding with 4 shards. Capacity is exhausted and you need to add a 5th shard. What happens?

> **Answer:** With naive `hash(key) % N`, changing N from 4 to 5 remaps `hash(key) % 5 ≠ hash(key) % 4` for approximately 4/5 = 80% of keys. All those keys must be migrated to new shards. This is operationally very expensive. Solution: use **consistent hashing** from the start — adding a 5th node moves only ~20% of keys (1/5), and only those adjacent on the ring.

---

**Q3.** A gaming company stores player data sharded by player_id. The most popular player in the game generates 100× more reads than average. What happens and how do you fix it?

> **Answer:** The shard containing this player's data becomes a **hotspot** — it receives 100× more traffic, its CPU/memory/network are saturated, while other shards are mostly idle. Fixes:
> - **Read caching**: cache the popular player's data in a CDN or Redis (serve most reads without hitting the shard DB)
> - **Dedicated shard**: move the popular player to a dedicated, higher-capacity shard
> - **Replica reads**: add read replicas for that specific shard, route reads round-robin across replicas
> - **Salting** (if this is a write hotspot too): store N copies with hash prefix, write to all, read from random one

---

**Q4.** Compare consistent hashing ring with Redis Cluster's hash slots approach.

> **Answer:**
> - **Consistent hashing ring**: keys map to positions on a 2³² ring, nodes own contiguous arcs. Adding a node takes adjacent arcs from neighbors. Supports arbitrary number of nodes. Cassandra/DynamoDB use this with vnodes.
> - **Redis Cluster hash slots**: 16,384 fixed slots, `CRC16(key) % 16384`. Slots are assigned to nodes. Simpler to reason about, no ring complexity. Adding a node moves N/16384 fraction of slots from each existing node. More manual management of slot assignments.
> - Both achieve the goal of minimal data movement on topology changes. Consistent hashing is more flexible; hash slots are simpler to implement and reason about.

---

**Q5.** Design the sharding strategy for a multi-tenant SaaS application where 90% of tenants are small (< 1 GB data) and 10% are large enterprises (10-100 GB each).

> **Answer:** Use a **tiered sharding strategy**:
> - **Small tenants** (90%): pack many tenants into shared shards, keyed by tenant_id. Each shared shard holds ~100-1000 small tenants. Total data per shard: ~100 GB.
> - **Large tenants** (10%): dedicated shard per large tenant, or internally shard by user_id within that tenant's namespace.
> - **Directory service**: maintain a mapping `tenant_id → shard_id`. Route all queries through this directory.
> - Benefits: large tenants can't impact small tenants (no noisy neighbor). Small tenants don't waste dedicated shard space. Large tenants can scale their shard independently.

---

## Key Concepts Checklist

- [ ] Vertical vs horizontal scaling: trade-offs, when to choose each
- [ ] Read replicas: 10× read scale-out before sharding
- [ ] Range sharding: efficient range queries, but hotspot on monotonic keys
- [ ] Hash sharding: uniform distribution, poor range queries, expensive rebalancing
- [ ] Consistent hashing: O(1/N) data movement on topology change
- [ ] Virtual nodes: uniform load distribution across physical nodes
- [ ] Shard key properties: high cardinality, immutable, even distribution, aligned with access patterns
- [ ] Cross-shard joins: co-location strategy or application-side scatter-gather
- [ ] Cross-shard transactions: 2PC (blocking) or SAGA (eventual)
- [ ] Hotspot mitigation: caching, salting, dedicated shards
