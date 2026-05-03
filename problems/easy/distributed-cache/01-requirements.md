# Step 1 — Requirements

## Functional Requirements

| # | Requirement | Notes |
|---|-------------|-------|
| F1 | GET(key) → value or null | O(1) time |
| F2 | SET(key, value, ttl?) | Evict LRU if full |
| F3 | DELETE(key) | Immediate removal |
| F4 | TTL per key | Lazy expiry + active sweep |
| F5 | Distribute across N nodes | Consistent hashing |

## Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| N1 | Low latency | p99 GET < 1 ms |
| N2 | High availability | Tolerate 1-2 node failures |
| N3 | Scalability | Add nodes without rehashing all keys |
| N4 | Memory efficiency | Compact encoding for small values |
| N5 | Cache hit rate | > 80 % for hot workloads |

## Clarifying Questions

1. "Is this a write-through or cache-aside model?"
2. "Should the cache be the source of truth, or is there a backing DB?"
3. "Is strong consistency needed, or is eventual consistency OK?"
4. "Should reads on cache miss block or return null immediately?"
5. "Do we need replication (hot standby) per node?"

## Scope for v1

- Single-tier in-memory key-value store
- LRU eviction
- Consistent hashing across nodes
- TTL with lazy expiry
- No replication (add in v2)
