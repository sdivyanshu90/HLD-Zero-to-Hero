# CPU Architecture Basics

## Why This Matters for System Design

Every distributed system decision — whether to cache, batch, parallelize, or offload — traces back to understanding what hardware can and cannot do cheaply. CPU architecture sets the fundamental cost model: what operations cost nanoseconds versus microseconds versus milliseconds.

---

## The Memory Hierarchy: The Single Most Important Mental Model

The CPU cannot process data that isn't in registers. It must fetch everything from somewhere. The hierarchy below is ordered from fastest to slowest, and the cost difference is enormous:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CPU MEMORY HIERARCHY                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  REGISTERS  (~0.3 ns)   ~1 KB   — in-flight computation  │   │
│  └─────────────────────┬────────────────────────────────────┘   │
│                         │                                         │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  L1 CACHE   (~1 ns)    32–64 KB  per core                 │  │
│  └─────────────────────┬────────────────────────────────────┘   │
│                         │                                         │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  L2 CACHE   (~4 ns)    256 KB–1 MB per core               │  │
│  └─────────────────────┬────────────────────────────────────┘   │
│                         │                                         │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  L3 CACHE   (~10–30 ns)  8–64 MB  shared across cores     │  │
│  └─────────────────────┬────────────────────────────────────┘   │
│                         │                                         │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  MAIN RAM   (~100 ns)   GBs      — DRAM                   │  │
│  └─────────────────────┬────────────────────────────────────┘   │
│                         │                                         │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  NVMe SSD   (~100 µs)   TBs      — persistent storage     │  │
│  └─────────────────────┬────────────────────────────────────┘   │
│                         │                                         │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  NETWORK    (~500 µs–100 ms)     — remote machine         │  │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### The Relative Cost Table

| Level       | Latency       | Relative to L1 | Human-scale analogy (1 L1 = 1 second) |
|-------------|---------------|-----------------|----------------------------------------|
| L1 Cache    | ~1 ns         | 1×              | 1 second                               |
| L2 Cache    | ~4 ns         | 4×              | 4 seconds                              |
| L3 Cache    | ~30 ns        | 30×             | 30 seconds                             |
| RAM         | ~100 ns       | 100×            | 1.7 minutes                            |
| NVMe SSD    | ~100 µs       | 100,000×        | 1.2 days                               |
| HDD         | ~10 ms        | 10,000,000×     | 4 months                               |
| Network LAN | ~500 µs       | 500,000×        | 6 days                                 |
| Network WAN | ~100 ms       | 100,000,000×    | 3 years                                |

> **Key insight**: A single cache miss to RAM costs as much as ~100 L1 hits. A network round trip costs as much as ~100,000 L1 hits. Keeping data local is a dominant system design principle.

---

## Multi-Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  MULTI-CORE CPU DIE                          │
│                                                              │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │   CORE 0     │        │   CORE 1     │                  │
│  │  ┌────────┐  │        │  ┌────────┐  │                  │
│  │  │  L1$   │  │        │  │  L1$   │  │                  │
│  │  └────────┘  │        │  └────────┘  │                  │
│  │  ┌────────┐  │        │  ┌────────┐  │                  │
│  │  │  L2$   │  │        │  │  L2$   │  │                  │
│  │  └────────┘  │        │  └────────┘  │                  │
│  └──────┬───────┘        └──────┬───────┘                  │
│         └────────────┬──────────┘                          │
│  ┌─────────────────────────────────────┐                   │
│  │       SHARED L3 CACHE               │                   │
│  └─────────────────┬───────────────────┘                   │
│                     │                                       │
│           MEMORY CONTROLLER  →  DRAM                       │
└─────────────────────────────────────────────────────────────┘
```

When two cores cache the same memory line and one writes to it, the MESI protocol (Modified/Exclusive/Shared/Invalid) must invalidate the other core's copy. This cross-core coherence traffic is expensive — **false sharing** (two unrelated variables sharing a cache line across cores) can reduce throughput by 10×.

---

## Branch Prediction

The CPU speculatively executes predicted branch paths. A misprediction flushes ~15–20 pipeline stages.

```
// Predictable — CPU predicts correctly almost every time
data.sort()
for item in data:
    if item > threshold:   ← once it flips, it stays flipped
        process(item)

// Unpredictable — 50/50 random branch, ~15 wasted cycles each
for item in random_order:
    if random_bit(item):   ← branch predictor is helpless
        process(item)
```

---

## Context Switching Cost

When the OS switches threads on a core, it must save/restore all registers and the thread's working set may no longer be in cache:

```
Lightweight context switch:    ~1–10 µs
Cache warm-up after switch:    10–100 µs

→ Event-loop models (Node.js, Nginx) avoid context switch by never blocking
→ Goroutines / green threads are cooperative and cheaper
→ Thread pool sizing: too many threads → too many context switches
```

---

## NUMA: Non-Uniform Memory Access

Large servers have multiple CPU sockets, each with its own local RAM:

```
NUMA Node 0           ←— QPI ~40ns —→   NUMA Node 1
  CPU 0 + RAM 0                            CPU 1 + RAM 1

Local DRAM:  ~100 ns
Remote DRAM: ~140 ns  (+40%)

→ Redis, RocksDB, Kafka pin threads to NUMA nodes
→ OS can NUMA-bind process memory for latency predictability
```

---

## Practical System Design Implications

| Design Decision          | Hardware Reasoning |
|--------------------------|--------------------|
| Local in-process cache   | Avoid 500µs network hop; RAM is 5000× cheaper |
| Batch I/O requests       | Amortize fixed RTT across many operations |
| Sequential scan over random access | CPU prefetching; full cache line utilization |
| Async I/O, event loop    | Avoid context switch overhead on I/O-bound work |
| Bloom filter before cache | 10ns local check vs 500µs remote lookup |
| Column-oriented storage  | Sequential reads exploit prefetcher for analytics |
| Lock-free ring buffers   | No cache coherence invalidation on writes |

---

## Interview Quick Answers

- **Why is Redis single-threaded?** — Avoids lock contention and cache coherence traffic; the bottleneck is network I/O, not CPU.
- **Why do databases use buffer pools?** — Keep hot disk pages in RAM (100ns vs 100µs = 1000× cheaper).
- **Why does Kafka prefer sequential disk writes?** — Sequential I/O saturates disk bandwidth; random I/O is ~100× slower.
- **Why use a bloom filter?** — Replace a 500µs cache lookup with a ~10ns probabilistic in-memory check.
