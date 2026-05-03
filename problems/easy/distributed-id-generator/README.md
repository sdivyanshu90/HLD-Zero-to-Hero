# Distributed ID Generator — System Design Walkthrough

**Difficulty:** Easy  
**Tags:** Snowflake, clock-skew, monotonicity, ZooKeeper  
**Companies:** Twitter (Snowflake), Instagram, Discord

---

## Problem Statement

Design a distributed unique ID generator that:
- Generates globally unique 64-bit IDs
- Is sortable by time (monotonically increasing)
- Generates ≥ 1 M IDs/sec across the cluster
- Operates without a central coordinator on the hot path
- Handles clock skew and leap seconds gracefully

---

## Snowflake 64-Bit Layout

```
 63       62                22               12            0
  │        │                 │                │             │
  ▼        ▼                 ▼                ▼             ▼
 [sign=0] [  timestamp 41b  ] [ machine_id 10b ] [ seq 12b  ]

sign      = 1 bit   (always 0; keeps IDs positive as signed int64)
timestamp = 41 bits = 2^41 ms ≈ 69 years from epoch
machine   = 10 bits = 1024 unique nodes
sequence  = 12 bits = 4096 IDs per ms per machine
```

**Max throughput:** 4 096 IDs/ms/machine × 1 000 ms/s = **4.096 M IDs/sec/machine**

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Throughput and Capacity](02-throughput-and-capacity.md)
3. [64-Bit Layout](03-64-bit-layout.md)
4. [Generation Flow](04-generation-flow.md)
5. [Clock Skew and Sequence Handling](05-clock-skew-and-sequence-handling.md)
6. [Checkpoint](06-checkpoint.md)
