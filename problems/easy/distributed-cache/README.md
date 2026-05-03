# Distributed Cache — System Design Walkthrough

**Difficulty:** Easy  
**Tags:** LRU, consistent-hashing, eviction, Redis, Memcached  
**Companies:** Meta (Memcache), Twitter, Uber, Netflix

---

## Problem Statement

Design a distributed in-memory cache that:
- Stores key-value pairs with optional TTL
- Supports GET / SET / DELETE operations
- Distributes data across N cache nodes
- Handles node failures gracefully
- Targets < 1 ms GET latency at the 99th percentile

---

## Architecture Diagram

```
Clients
   │
   ▼
┌─────────────────────────────┐
│      Cache Client Library   │  consistent hash ring, connection pool
└─────────────────────────────┘
         │          │          │
         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │ Node 0 │ │ Node 1 │ │ Node 2 │  (Redis / Memcached instances)
    │  RAM   │ │  RAM   │ │  RAM   │
    └────────┘ └────────┘ └────────┘
         │
    optional persistence
         ▼
    ┌────────┐
    │  Disk  │  RDB snapshot / AOF log (Redis only)
    └────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [API Surface](02-api-surface.md)
3. [Core Data Structures](03-core-data-structures.md)
4. [Eviction Policy](04-eviction-policy.md)
5. [Persistence Options](05-persistence-options.md)
6. [Distribution and Scaling](06-distribution-and-scaling.md)
7. [Checkpoint](07-checkpoint.md)
