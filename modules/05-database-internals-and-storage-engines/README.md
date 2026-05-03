# Module 05: Database Internals and Storage Engines

## Overview

This module looks under the hood of databases. Understanding how data is stored and retrieved lets you predict performance, make informed index decisions, and choose the right database for your workload.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│          MODULE 05 LEARNING MAP                                 │
│                                                                  │
│  01-b-trees                                                     │
│     └── B+ tree structure, node layout, height calculation     │
│         Read path (4-5 I/Os), write path, range scans          │
│                    │                                            │
│                    ▼                                            │
│  02-lsm-trees                                                   │
│     └── WAL → MemTable → L0 → L1... (compaction chain)        │
│         Bloom filters, SSTable format, tombstones              │
│                    │                                            │
│                    ▼                                            │
│  03-write-path-components                                       │
│     └── WAL internals, group commit, buffer pool               │
│         MemTable skip list, dirty page flushing                │
│                    │                                            │
│                    ▼                                            │
│  04-compaction-and-bloom-filters                                │
│     └── STCS vs LCS vs TWCS trade-offs                         │
│         Bloom filter math (false positive rate, bits/key)      │
│         HyperLogLog, Count-Min Sketch                          │
│                    │                                            │
│                    ▼                                            │
│  05-engine-selection                                            │
│     └── B-Tree vs LSM vs Columnar vs Specialized               │
│         Decision framework, real-world system choices          │
└────────────────────────────────────────────────────────────────┘
```

---

## B-Tree vs LSM Summary

```
Metric               B-Tree (PostgreSQL)    LSM (Cassandra)
───────────────────────────────────────────────────────────
Write latency        Low (in-place)         Very low (append)
Write throughput     Moderate              Very high
Read latency         Very low              Low-medium
Space efficiency     High                  Medium-high
Compaction needed    No (VACUUM)           Yes (critical)
ACID transactions    Yes                   Limited
Best workload        Mixed OLTP            Write-heavy append
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-b-trees.md](01-b-trees.md) | B+ tree structure, reads, writes |
| [02-lsm-trees.md](02-lsm-trees.md) | LSM tree, MemTable, SSTables, compaction |
| [03-write-path-components.md](03-write-path-components.md) | WAL, buffer pool, group commit |
| [04-compaction-and-bloom-filters.md](04-compaction-and-bloom-filters.md) | Compaction strategies, bloom filters |
| [05-engine-selection.md](05-engine-selection.md) | Engine choice framework |
| [06-checkpoint.md](06-checkpoint.md) | Self-test questions |
