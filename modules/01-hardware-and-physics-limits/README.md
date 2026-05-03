# Module 01: Hardware and Physics Limits

## Why Start Here?

System design is not magic — it is bounded by physics. Every design decision you make in an interview (use a cache here, shard this data, batch those writes) has a hardware justification. This module builds the mental model that lets you reason from first principles rather than memorizing patterns.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────┐
│              MODULE 01 LEARNING MAP                         │
│                                                             │
│  01-cpu-architecture-basics                                 │
│     └── Memory hierarchy, cache levels, branch prediction  │
│         Multi-core, NUMA, context switching                 │
│                    │                                        │
│                    ▼                                        │
│  02-latency-numbers                                         │
│     └── L1=1ns, RAM=100ns, SSD=100µs, Network=500µs        │
│         The gaps that drive every architecture decision     │
│                    │                                        │
│                    ▼                                        │
│  03-throughput-vs-latency                                   │
│     └── Little's Law, Amdahl's Law, queuing theory         │
│         Why they trade off, how to balance them            │
│                    │                                        │
│                    ▼                                        │
│  04-data-locality-and-batching                              │
│     └── Temporal/spatial locality, co-location             │
│         Batching patterns, CDN, denormalization            │
│                    │                                        │
│                    ▼                                        │
│  05-hardware-trade-offs-in-design                           │
│     └── Compute vs Memory vs Storage vs Network            │
│         Real-world decisions explained by hardware         │
└────────────────────────────────────────────────────────────┘
```

---

## The 10 Numbers You Must Know Cold

| Operation | Latency |
|-----------|---------|
| L1 cache hit | 1 ns |
| L2 cache hit | 4 ns |
| RAM access | 100 ns |
| SSD random read | 100 µs |
| Same-datacenter round trip | 500 µs |
| HDD seek | 10 ms |
| Cross-continent round trip | 150 ms |
| Compress 1 KB (Snappy) | 3 µs |
| Sequential RAM throughput | 10 GB/s |
| Sequential SSD throughput (NVMe) | 3 GB/s |

---

## Core Principles This Module Establishes

1. **Data locality wins**: every layer of the hierarchy is orders of magnitude apart
2. **Sequential > random** at every storage level
3. **Amortize fixed costs**: batching is almost always worth it at scale
4. **Trade resources deliberately**: cache = memory for speed; compression = CPU for storage
5. **Design at 60-70% utilization**: queuing theory makes 90%+ catastrophic

---

## How This Connects to Other Modules

- **Module 06 (Scaling)**: vertical vs horizontal scaling is bounded by these limits
- **Module 08 (Caching)**: cache tiers exist precisely because of the memory hierarchy
- **Module 09 (Messaging)**: Kafka's sequential write model is justified here
- **Module 05 (DB Internals)**: LSM trees and B-trees make different latency/throughput choices
- **Module 11 (BoE Math)**: all estimations start from these latency numbers

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-cpu-architecture-basics.md](01-cpu-architecture-basics.md) | CPU, caches, pipeline, NUMA |
| [02-latency-numbers-every-programmer-should-know.md](02-latency-numbers-every-programmer-should-know.md) | The canonical latency table with analysis |
| [03-throughput-vs-latency.md](03-throughput-vs-latency.md) | Little's Law, queuing theory, Amdahl's Law |
| [04-data-locality-and-batching.md](04-data-locality-and-batching.md) | Locality types, batching patterns, co-location |
| [05-hardware-trade-offs-in-design.md](05-hardware-trade-offs-in-design.md) | Real trade-offs: memory vs compute, disk vs RAM |
| [06-checkpoint.md](06-checkpoint.md) | Self-test questions and key numbers |
