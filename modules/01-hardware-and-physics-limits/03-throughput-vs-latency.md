# Throughput vs Latency

## Definitions

**Latency** is the time from when a request is issued to when the response is received. It is a *per-request* measurement.

**Throughput** is the number of requests (or units of work) completed per unit of time. It is a *system-level* measurement.

```
Latency:   |──── request time ────|
           Send ────────────────▶ Receive
           t=0                   t=50ms   → Latency = 50ms

Throughput: ────────────────────────────▶ time
            req1 req2 req3 req4 req5
            ↕↕↕↕  (per second)           → Throughput = 5 req/s
```

---

## The Tension Between Them

Latency and throughput often conflict. Optimizing one can hurt the other:

```
┌─────────────────────────────────────────────────────────────┐
│                 LATENCY vs THROUGHPUT TRADE-OFF              │
│                                                              │
│   Single request, no batching:                              │
│   Request ──────────────────▶ Response                      │
│   Latency: LOW ✓   Throughput: LOW ✗                        │
│                                                              │
│   Batched requests:                                          │
│   [req1+req2+req3+req4] ────▶ [resp1+resp2+resp3+resp4]     │
│   Latency: HIGH ✗  Throughput: HIGH ✓                       │
│                                                              │
│   Optimal: find the batch size where throughput is          │
│   maximized without violating latency SLAs                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Little's Law

Little's Law is the fundamental equation linking latency, throughput, and concurrency:

```
L = λ × W

L = average number of requests in the system (concurrency)
λ = average arrival rate (throughput, req/s)
W = average time a request spends in the system (latency, seconds)

Rearranged:
  Throughput = Concurrency / Latency
  Latency    = Concurrency / Throughput
  Concurrency = Throughput × Latency
```

### Worked Example

```
System handles 1,000 req/s
Average latency is 200ms (0.2 s)

Concurrency = 1,000 × 0.2 = 200 concurrent requests in flight

If latency doubles to 400ms:
  With same concurrency (200): throughput drops to 200/0.4 = 500 req/s
  To maintain 1,000 req/s: need 1,000 × 0.4 = 400 concurrent slots
```

> **System design use**: If you know your throughput target and latency budget, Little's Law tells you how much concurrency (threads, connections, queue depth) you need.

---

## Latency Percentiles: Why Averages Lie

Averages hide the worst user experiences. Always report P50, P95, P99, P99.9:

```
Example latency distribution (1,000 requests):
  P50  (median):    20ms   — 500 users saw this or better
  P95:              85ms   — 950 users saw this or better
  P99:             200ms   — 990 users saw this or better
  P99.9:           800ms   — 999 users saw this or better
  Max:            1,200ms  — 1 user saw this

Average: (500×20 + 450×85 + 40×200 + 9×800 + 1×1200) / 1000 ≈ 62ms

The "average" of 62ms hides the fact that 1% of users waited 200ms+
For 1M req/day → 10,000 users experience 200ms+ latency daily!
```

```
Distribution shape:
    ╭───╮
    │   │
    │   │
────┘   ╰──────────────────────────────────────╮──── latency
   20ms  85ms               200ms         800ms 1200ms
   P50   P90                P99          P99.9  max

Long tail: real systems always have this shape
```

---

## Throughput Ceiling: Amdahl's Law

When parallelizing work, the serial (non-parallelizable) fraction limits maximum speedup:

```
Speedup = 1 / (S + (1-S)/N)

S = fraction of work that is serial (cannot be parallelized)
N = number of parallel workers

If S = 0.05 (5% serial):
  N=2:   1/(0.05 + 0.95/2)   = 1.90× speedup
  N=10:  1/(0.05 + 0.95/10)  = 6.9× speedup
  N=100: 1/(0.05 + 0.95/100) = 16.8× speedup
  N=∞:   1/0.05              = 20× maximum ever

If S = 0.25 (25% serial):
  N=∞: maximum speedup = 4×
```

```
Throughput vs Workers (S=10%):

Throughput │                     ╭──── theoretical max (10×)
           │                 ╭───
           │             ╭───
           │         ╭───
           │     ╭───
           │ ╭───
           └──────────────────────────────▶ Workers
             1   2   4   8  16  32  64

→ Adding more servers hits diminishing returns
→ The coordination/serial overhead (S) is the true bottleneck
```

---

## Queuing Theory: How Queues Form

When arrival rate approaches service rate, queues grow non-linearly:

```
Utilization (ρ) = arrival rate / service rate

Queue depth:

ρ=0.5:  short queue
ρ=0.8:  noticeable queue
ρ=0.9:  long queue
ρ=0.95: very long queue
ρ=1.0:  infinite queue — system collapses!

Queue Length ≈ ρ² / (1 - ρ)   [M/M/1 model]

ρ=0.5: L = 0.5
ρ=0.8: L = 3.2
ρ=0.9: L = 8.1
ρ=0.95: L = 18
ρ=0.99: L = 98
```

```
Queue Growth (non-linear!)

Queue  │                                    /
depth  │                                  /
       │                                /
       │                            __/
       │                       ___/
       │               ______/
       └──────────────────────────────────▶
                                    1.0  Utilization
```

> **System design implication**: Design for peak utilization of 60–70%, not 90–100%. The non-linear queue growth at high utilization makes latency spikes catastrophic.

---

## Throughput Optimization Patterns

### Batching

```
Without batching (1 disk write per request):
  1,000 req/s × 1 write = 1,000 IOPS needed

With batching (group 100 requests per write):
  1,000 req/s / 100 = 10 IOPS needed
  Throughput same, disk load reduced 100×
```

### Pipelining

```
Without pipelining:
  send req1 ──▶ wait for resp1 ──▶ send req2 ──▶ wait for resp2
  Latency: 2 × RTT, Throughput: 0.5 req/RTT

With pipelining:
  send req1 ──▶ send req2 ──▶ send req3 ──▶
                resp1 ◀──── resp2 ◀──── resp3 ◀────
  Latency: ~1 RTT per req, Throughput: N req/RTT
```

### Concurrency (Parallelism)

```
1 thread, 100ms latency/request:        10 req/s
10 threads, 100ms latency/request:     100 req/s
100 threads, 100ms latency/request:  1,000 req/s  (but 100× memory!)
Async I/O, 100ms latency/request:  ~10,000 req/s  (1 thread!)
```

---

## Real-World Trade-off Table

| System         | Optimized For | Sacrifice      |
|----------------|---------------|----------------|
| HFT (trading)  | Latency       | Throughput, cost |
| Kafka          | Throughput    | Latency (batching adds ms) |
| Memcached      | Both (simple ops) | Durability |
| Spark batch job | Throughput   | Latency (minutes) |
| Redis Pub/Sub  | Latency       | Ordering, durability |
| OLTP DB        | Low latency   | Throughput per machine |
| OLAP / DWH     | High throughput | Latency (queries take seconds) |

---

## Interview Quick Answers

- **How do you increase throughput?** — Parallelism, batching, pipelining, reducing per-request work.
- **How do you reduce latency?** — Caching, precomputation, reducing hops, co-location, async operations.
- **Why do they conflict?** — Batching increases throughput by amortizing overhead, but the first request in a batch must wait for the batch to fill.
- **What utilization should I target?** — 60–70% for latency-sensitive systems; queuing theory shows non-linear degradation above 80%.
