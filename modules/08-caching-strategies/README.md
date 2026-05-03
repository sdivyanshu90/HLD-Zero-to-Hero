# Module 08: Caching Strategies

## Overview

Caching is the single highest-leverage optimization in system design. A well-placed cache can reduce database load by 95%+, reduce latency from 10ms to 0.5ms, and increase throughput by orders of magnitude.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│              MODULE 08 LEARNING MAP                             │
│                                                                  │
│  01-cache-tiers-and-placement                                   │
│     └── CPU/OS → In-process → Redis → CDN                     │
│         Redis vs Memcached decision                            │
│                    │                                            │
│                    ▼                                            │
│  02-eviction-policies                                           │
│     └── LRU (temporal), LFU (frequency), ARC (adaptive)        │
│         TinyLFU (Caffeine), TTL                                │
│                    │                                            │
│                    ▼                                            │
│  03-write-policies                                              │
│     └── Write-through (consistent), write-behind (fast)        │
│         Cache-aside (most common), thundering herd             │
│                    │                                            │
│                    ▼                                            │
│  04-cache-failure-modes                                         │
│     └── Stampede, avalanche, penetration, hot key             │
│         Bloom filters, circuit breakers, key sharding          │
└────────────────────────────────────────────────────────────────┘
```

---

## Cache Decision Framework

```
Should I cache this data?
  ✓ Frequently read, rarely written?          → YES
  ✓ Read is expensive (DB query > 5ms)?       → YES
  ✓ Data freshness tolerance > 0?             → YES
  ✗ User-specific private data?               → Be careful (cache isolation)
  ✗ Financial / inventory data?               → Be careful (stale = dangerous)
  ✗ Unique request that won't repeat?         → NO

Where to cache?
  Need < 1µs? sub-process data → in-process cache
  Shared across N app servers? → Redis
  Global (CDN)?  → Public, static, or API responses with max-age
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-cache-tiers-and-placement.md](01-cache-tiers-and-placement.md) | Cache hierarchy, Redis vs Memcached |
| [02-eviction-policies.md](02-eviction-policies.md) | LRU, LFU, ARC, TinyLFU, TTL |
| [03-write-policies.md](03-write-policies.md) | Write-through, write-behind, cache-aside |
| [04-cache-failure-modes.md](04-cache-failure-modes.md) | Stampede, avalanche, penetration |
| [05-checkpoint.md](05-checkpoint.md) | Self-test questions |
