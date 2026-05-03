# Module 01 Checkpoint: Hardware and Physics Limits

## Concepts to Confirm Before Moving On

Answer each question from memory before checking. These are the exact types of questions that come up in senior interviews.

---

## Core Questions

**Q1.** A service has P99 latency of 50ms. An engineer proposes adding a synchronous call to a service in another region (150ms RTT). What happens to P99 latency and why?

> **Answer:** P99 latency becomes at least 200ms (50ms + 150ms). The cross-region call is serialized in the critical path. Even if the call succeeds, the physics of 150ms RTT cannot be avoided. Solution: make the call async, replicate data regionally, or tolerate eventual consistency.

---

**Q2.** You have 10,000 req/s hitting your service, each taking 20ms to process. Using Little's Law, how many concurrent requests are in flight?

> **Answer:** L = λ × W = 10,000 req/s × 0.020 s = **200 concurrent requests**.

If you use a thread-per-request model, you need at least 200 threads. If latency doubles to 40ms, you need 400 threads to handle the same throughput.

---

**Q3.** Why does Kafka achieve high throughput by writing to disk, even though disk is slower than RAM?

> **Answer:** Kafka writes **sequentially** to disk. Sequential disk I/O on modern SSDs delivers ~500 MB/s–3 GB/s throughput, comparable to sequential RAM operations for large blocks. The OS page cache also serves reads from RAM when data is recently written. By avoiding random I/O entirely, Kafka sidesteps the 10ms seek cost of rotational disk.

---

**Q4.** What is false sharing and why does it hurt multi-core performance?

> **Answer:** False sharing occurs when two threads on different CPU cores write to *different variables* that happen to reside on the *same cache line* (typically 64 bytes). The MESI protocol must invalidate the other core's cache line on every write, causing expensive cache coherence traffic even though the threads are accessing unrelated data. Fix: pad structs so hot variables are on separate cache lines.

---

**Q5.** At 80% utilization, approximately how deep is the queue for an M/M/1 system?

> **Answer:** L = ρ² / (1-ρ) = 0.64 / 0.20 = **3.2 items**. At 90% utilization: 8.1 items. At 95%: 18 items. This non-linear growth is why you should target 60-70% utilization, not 90%+.

---

## Design Challenges

**Challenge 1:** Design a system that aggregates click events from 10,000 sources, storing the last 7 days of data, with P99 query latency under 10ms.

Key hardware decisions to justify:
- What storage tier holds the data?
- What data layout enables 10ms queries?
- How do you handle the write throughput (10K sources × events/sec)?

---

**Challenge 2:** Your read-heavy service (95% reads, 5% writes) has 500ms P99 latency. Database CPU is at 90%. What hardware trade-off do you make?

> Consider: caching (RAM trade for DB CPU), read replicas (add machines to distribute reads), denormalization (disk/storage trade for CPU savings), connection pooling (reduce connection overhead).

---

## Numbers to Memorize

```
L1 cache:        1 ns
L2 cache:        4 ns
RAM:           100 ns
Same-DC round trip:  500 µs
SSD random read:     100 µs
Cross-region RTT:    100–150 ms
```

---

## Key Principles Checklist

- [ ] Memory hierarchy: registers → L1 → L2 → L3 → RAM → SSD → Network
- [ ] Little's Law: Concurrency = Throughput × Latency
- [ ] Queuing theory: non-linear queue growth above 80% utilization
- [ ] Batching amortizes fixed costs (network RTT, disk seek, lock acquisition)
- [ ] Sequential I/O is always faster than random I/O at every storage tier
- [ ] Amdahl's Law: serial fraction caps parallel speedup
- [ ] Latency percentiles (P50/P95/P99) are more useful than averages
