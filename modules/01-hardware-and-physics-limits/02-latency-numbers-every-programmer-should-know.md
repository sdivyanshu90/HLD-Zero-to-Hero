# Latency Numbers Every Programmer Should Know

## The Canonical Table (2024 Approximations)

These numbers change slightly with hardware generations but the *orders of magnitude* remain stable. Memorize the orders of magnitude, not the exact values.

| Operation                                  | Latency        | Notes |
|--------------------------------------------|----------------|-------|
| CPU register access                        | 0.3 ns         | In-flight computation |
| L1 cache hit                               | 1 ns           | Per core |
| Branch misprediction penalty               | 5 ns           | Flushed pipeline |
| L2 cache hit                               | 4 ns           | Per core |
| L3 cache hit                               | 10–30 ns       | Shared across cores |
| Mutex lock/unlock                          | 25 ns          | Uncontended |
| Main memory (DRAM) access                  | 100 ns         | Random access |
| Compress 1 KB with Snappy                  | 3,000 ns       | 3 µs |
| Send 1 KB over 1 Gbps network              | 10,000 ns      | 10 µs |
| Read 4 KB randomly from SSD               | 100,000 ns     | 100 µs |
| Read 1 MB sequentially from RAM            | 250,000 ns     | 250 µs |
| Round trip within same datacenter          | 500,000 ns     | 500 µs |
| Read 1 MB sequentially from SSD           | 1,000,000 ns   | 1 ms |
| Disk seek (rotational HDD)                 | 10,000,000 ns  | 10 ms |
| Read 1 MB sequentially from HDD           | 30,000,000 ns  | 30 ms |
| Send packet CA → Netherlands → CA (WAN)   | 150,000,000 ns | 150 ms |

---

## Visualization: Orders of Magnitude

```
ns   ──────────────────────────────────────────────────────────────▶
      │
    1 │ L1 cache
   10 │ L2/L3 cache, mutex
  100 │ RAM access
      │
µs   ──────────────────────────────────────────────────────────────▶
    1 │ (nothing useful happens here in most systems)
   10 │ Send 1KB on network
  100 │ NVMe SSD random read
  500 │ Same-datacenter round trip
      │
ms   ──────────────────────────────────────────────────────────────▶
    1 │ NVMe sequential read (1 MB)
   10 │ HDD seek
  100 │ Cross-continent round trip
      │
  s  ──────────────────────────────────────────────────────────────▶
```

---

## The Big Gaps That Drive Architecture Decisions

### Gap 1: RAM vs Network (500×)

```
RAM access:        100 ns
Same-DC network:   500 µs  (500× slower)

→ One network hop = 5,000 RAM accesses
→ Justifies: local caches, compute-at-origin, denormalization
```

### Gap 2: SSD vs RAM (1,000×)

```
RAM access:      100 ns
SSD random:      100 µs  (1,000× slower)

→ Every disk read avoided = 1,000 RAM operations saved
→ Justifies: buffer pools, write-ahead logs, memory-mapped files
```

### Gap 3: RAM vs Disk Sequential (10,000×)

```
RAM sequential:    250 µs / MB
HDD sequential:    30 ms  / MB  (120× slower per MB)
HDD random:        10 ms  per seek + data read

→ Justifies: sequential-write-only architectures (LSM trees, Kafka)
→ Justifies: log-structured file systems and append-only patterns
```

### Gap 4: Intra-DC vs Inter-DC (300×)

```
Same datacenter:   500 µs
Cross-continent:   150 ms  (300× slower)

→ Justifies: regional data residency, read replicas in local region
→ Justifies: async cross-region replication (eventual consistency)
```

---

## Applied: Designing for Latency Targets

### SLA of 10 ms (P99)

```
Budget: 10,000 µs total

Allowed:
  - ~5 network hops within datacenter    (5 × 500 µs = 2,500 µs)
  - ~1 SSD random read                   (100 µs)
  - ~50 RAM operations                   (5 µs)
  - Processing overhead                  (7,395 µs)

NOT allowed:
  - Cross-region database read           (150 ms >> budget)
  - Synchronous fan-out to 20 services   (20 × 500 µs = 10 ms alone)
```

### SLA of 100 ms (P99)

```
Budget: 100,000 µs total

Allowed:
  - 1 cross-region read                  (150 ms — borderline, risky)
  - Up to 100 same-DC round trips        (100 × 500 µs = 50 ms)
  - Multiple SSD reads                   (each 100 µs)
```

---

## Memory Bandwidth Numbers

| Operation                  | Throughput    |
|----------------------------|---------------|
| L3 cache bandwidth         | ~200 GB/s     |
| DRAM bandwidth (DDR5)      | ~50–100 GB/s  |
| NVMe SSD sequential read   | ~7 GB/s       |
| NVMe SSD sequential write  | ~6 GB/s       |
| 10 Gbps network            | ~1.2 GB/s     |
| 100 Gbps network (modern)  | ~12 GB/s      |

> **Key insight**: Modern NVMe SSDs are faster than 10 Gbps NICs at sequential reads. Network is now often the storage bottleneck in distributed systems.

---

## Network Throughput vs Latency

Latency and throughput are independent dimensions:

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  Throughput                                        │
│  (GB/s)   High │  Big file transfer    ← ideal     │
│                │  (high BW, low lat)               │
│           Low  │  Chat messages                    │
│                │  (low BW, low lat)                │
│                └──────────────────────────────────▶│
│                   Low            High   Latency    │
│                                                    │
│  Most database queries: low BW, want low latency   │
│  Video streaming: high BW, tolerates some latency  │
│  HFT trading: extremely low latency, low BW        │
└────────────────────────────────────────────────────┘
```

---

## Interview Quick Answers

- **How many requests can a server handle?** — Depends on latency of each. If each request takes 1ms and you have 1 thread per request, 1 thread can do 1,000 req/s. With async I/O and 1,000 concurrent I/Os, same thread does 1,000,000 req/s.
- **Is a 500ms DB query acceptable?** — Only if the user-facing SLA is >1s. P99 user-perceived latency should be under 200ms for web apps.
- **Why is cross-region synchronous replication risky?** — 150ms RTT means every write blocks for 150ms minimum — unacceptable for most workloads.
