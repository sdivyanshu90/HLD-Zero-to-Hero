# Module 06: Scaling and Partitioning

## Overview

At some point, every successful system outgrows a single database node. This module covers the spectrum of scaling approaches and the mechanics of distributing data across multiple machines.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│              MODULE 06 LEARNING MAP                             │
│                                                                  │
│  01-vertical-vs-horizontal-scaling                              │
│     └── Scale up vs scale out trade-offs                       │
│         The staircase: cache → replicas → vertical → shard     │
│                    │                                            │
│                    ▼                                            │
│  02-sharding-strategies                                         │
│     └── Range, Hash, Directory-based partitioning              │
│         Cross-shard joins, transactions, hotspots              │
│                    │                                            │
│                    ▼                                            │
│  03-consistent-hashing                                          │
│     └── Ring, virtual nodes, rebalancing                       │
│         DynamoDB, Cassandra, Redis Cluster implementations     │
│                    │                                            │
│                    ▼                                            │
│  04-shard-key-selection                                         │
│     └── Good/bad shard key properties                          │
│         Domain-specific examples, hotspot mitigation           │
│                    │                                            │
│                    ▼                                            │
│  05-rebalancing                                                 │
│     └── Handoff protocol, streaming throttling                 │
│         Double-write migration for hash sharding               │
└────────────────────────────────────────────────────────────────┘
```

---

## The Scaling Decision Tree

```
Is the system slow?
  ↓
Optimize queries and add indexes first
  ↓ (still slow?)
Add Redis caching for hot reads
  ↓ (still slow?)
Add read replicas (scale reads 4-10×)
  ↓ (still slow?)
Vertical scale the primary (more RAM/CPU)
  ↓ (still slow? or data too large?)
Table partitioning (no distributed complexity!)
  ↓ (still insufficient?)
Horizontal sharding (distributed system!)
  Choose shard key carefully — hard to change later
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-vertical-vs-horizontal-scaling.md](01-vertical-vs-horizontal-scaling.md) | Scale-up vs scale-out, read replicas |
| [02-sharding-strategies.md](02-sharding-strategies.md) | Range/hash/directory sharding |
| [03-consistent-hashing.md](03-consistent-hashing.md) | Ring, vnodes, real implementations |
| [04-shard-key-selection.md](04-shard-key-selection.md) | Shard key design, hotspots |
| [05-rebalancing.md](05-rebalancing.md) | Rebalancing protocols and migration |
| [06-checkpoint.md](06-checkpoint.md) | Self-test questions |
