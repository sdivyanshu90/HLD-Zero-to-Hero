# Step 6 — Checkpoint & Interview Q&A

**Q1: Why not use UUID v4?**
> UUIDs are 128-bit, not time-sortable, and random — terrible for DB index locality (B-tree random inserts = page splits = slow). Snowflake IDs are 64-bit, time-prefixed, and maintain insert locality in B-tree indexes.

**Q2: How do you assign worker IDs without conflicts?**
> Use ZooKeeper sequential ephemeral znodes or etcd leases. Each node creates a lease on `/workers/{id}`, keeps renewing it. If the node crashes the lease expires, freeing the ID for another node. Prevents two nodes sharing the same worker_id.

**Q3: What is the maximum throughput of a single Snowflake node?**
> 4096 IDs per millisecond = 4.096 M IDs/sec. At this rate, the sequence counter saturates in each millisecond and the generator busy-waits for the next tick. At real-world loads of ~100K IDs/sec, saturation never occurs.

**Q4: How do you handle a 50ms clock jump backward after NTP sync?**
> For small jumps (< 5ms): spin-wait. For larger jumps: the generator rejects ID generation and returns an error (ClockBackwardError). Upstream callers retry. Meanwhile chrony/NTP gradually slews the clock forward; the generator recovers within seconds.

**Q5: If you need more than 1024 machines, how do you extend the layout?**
> Reduce the sequence bits: use 13 bits for worker (8192 nodes) and 10 bits for sequence (1024/ms). Or add a second tier of IDs where generator service manages a pool of (datacenter_id, worker_id) combos. Or use 128-bit IDs (ULID).

## Design Variants

| Variant | Change |
|---------|--------|
| Database auto-increment | Simple but single point of failure; can't scale horizontally |
| UUID v1 | Time-based, 128-bit, node MAC address embedded |
| Segment ranges | DB allocates ranges (e.g., 1-1000) to each node offline |
| Minter service | Centralised service, high throughput via in-memory counter, backed by ZooKeeper |
