# Data Locality and Batching

## Principle: Bring Computation to Data, Not Data to Computation

The single most powerful optimization in distributed systems is reducing the distance data must travel. Every byte moved between CPU and RAM, RAM and disk, or machine and machine has a cost. Designing for **data locality** minimizes these crossings.

---

## Types of Locality

### Temporal Locality

The same data is accessed repeatedly within a short window. This is why caches work:

```
Request pattern:
  t=0:   GET user:1234   → cache MISS → fetch from DB (100ms)
  t=1s:  GET user:1234   → cache HIT  → return (1ms) ← 100× faster
  t=2s:  GET user:1234   → cache HIT  → return (1ms)
  t=3s:  GET user:1234   → cache HIT  → return (1ms)

If user:1234 is accessed 100 times:
  Without cache:  100 × 100ms = 10,000ms total
  With cache:     1 × 100ms + 99 × 1ms = 199ms total  (50× improvement)
```

### Spatial Locality

Data that is physically adjacent in memory/storage tends to be accessed together. This is why sequential I/O is faster:

```
Array traversal (spatial locality — good):
  [1][2][3][4][5][6][7][8]
   ↑──────────────────────▶ sequential, prefetchable

Linked list traversal (poor spatial locality — bad):
  Node1 ──▶ Node4 ──▶ Node2 ──▶ Node7
   (scattered in memory, no prefetching possible)

Performance difference: 10–40× for large datasets
```

### Computational Locality

Running code on the same machine as the data it needs:

```
BAD (data crossing the network):
  Service A                    DB Server
  ┌──────────┐                ┌──────────┐
  │  Process │ ──GET data──▶  │  Data    │
  │  result  │ ◀──100KB────   │  Store   │
  └──────────┘                └──────────┘
  RTT: 500µs, 100KB transfer: ~100µs → 600µs total

GOOD (push computation to data — stored procedure / map-reduce):
  DB Server
  ┌──────────────────────────┐
  │  Data  +  Process code   │
  │  result computed locally │
  └──────────────────────────┘
  Return only 1 byte result → 500µs RTT, minimal data
```

---

## Batching: Amortizing Fixed Costs

Every operation has a **fixed overhead** component (setup, network RTT, lock acquisition) and a **variable** component (proportional to data size). Batching amortizes fixed costs:

```
Fixed cost model:
  Cost(N items) = Fixed_cost + N × Variable_cost

Without batching (N=1 per call):
  Total = 1,000 × (Fixed_cost + 1 × Variable_cost)
        = 1,000 × Fixed_cost + 1,000 × Variable_cost

With batching (N=100 per call):
  Total = 10 × (Fixed_cost + 100 × Variable_cost)
        = 10 × Fixed_cost + 1,000 × Variable_cost
        ← Fixed cost reduced 100×, variable cost same!
```

### Network Batching Example

```
Sending 1,000 small messages:
  Per-message RTT:  1,000 × 500µs = 500ms total wait
  Batched (100/batch): 10 × 500µs = 5ms total wait  (100× better)

  But: first message waits up to 500µs for batch to fill
  → Latency increases (500µs per message), throughput increases massively
```

### Disk Write Batching (Write-Ahead Log)

```
Application writes:
  write(user=1, data=...)  → needs to be durable (fsync)
  write(user=2, data=...)  → needs to be durable
  write(user=3, data=...)  → needs to be durable

Naive: 3 fsyncs × 5ms each = 15ms

WAL Group Commit:
  Buffer 3 writes → 1 fsync → all 3 are durable
  = 5ms total  (3× improvement)
  At higher write rates: 1000 writes in one fsync = 5000× improvement
```

---

## Co-location Strategies

### 1. Shard by Access Pattern (Hot Data Together)

```
BAD (user data split across shards by user ID):
  User:1   → Shard A
  User:2   → Shard B
  User:1's posts → Shard C  ← different shard!

  Viewing a user's profile page requires hitting 3 different shards

GOOD (shard by tenant / user locality):
  User:1 + User:1's posts + User:1's friends → Shard A
  User:2 + User:2's posts + User:2's friends → Shard B

  Viewing user:1's profile = 1 shard lookup
```

### 2. Read Replicas in the Same Region

```
Global:          Primary DB (us-east-1)
                 ↓ async replication
Regions:         Replica (eu-west-1)    ← EU users read locally
                 Replica (ap-east-1)    ← APAC users read locally

Without replicas: EU user reads from us-east → 100ms RTT
With replica:     EU user reads from eu-west →   5ms RTT
```

### 3. Cache Warming and Prefetching

```
Cold start problem:
  New server comes up → cache is empty → all requests hit DB
  DB gets spike → latency spikes → cascading failure

Solutions:
  a) Warm cache from snapshot on startup
  b) Prefetch predicted next pages (pagination: user views page 1 → prefetch page 2)
  c) Gradual traffic shifting: ramp new servers from 1% → 10% → 100%
```

---

## Data Locality Patterns in Distributed Systems

### 1. Push Down Computation (MapReduce / Spark)

```
OLAP query: "Sum of revenue by country for all orders"

BAD (pull all data to query engine):
  1TB orders table → network → query engine → aggregate
  Network transfer: 1TB × 1 Gbps = ~8,000 seconds!

GOOD (push computation to storage nodes):
  Shard 1: aggregate locally → send {US: $1M, UK: $200K}
  Shard 2: aggregate locally → send {US: $800K, DE: $300K}
  ...
  Query engine: merge 100 small results → microseconds

  Total network: 100 shards × 1KB result = 100KB  (10,000,000× less!)
```

### 2. Content Delivery Networks (CDNs)

```
Without CDN:
  User in Tokyo ──────────────────────▶ Origin (New York)
                        150ms RTT

With CDN:
  User in Tokyo ──▶ Tokyo CDN POP ──▶ Origin (New York)
                    5ms RTT     (only for cache miss, ~1% of requests)
  99% of requests served in 5ms instead of 150ms
```

### 3. Denormalization: Duplicate Data for Read Locality

```
Normalized (join required):
  users table: {id, name, email}
  posts table: {id, user_id, content, created_at}

  Read posts with author info → JOIN across two tables
  → 2 index lookups, potential disk seeks

Denormalized:
  posts table: {id, user_id, user_name, user_avatar, content, created_at}
  → 1 table read, no join needed
  → At cost: write amplification (update user changes many rows)
```

---

## Batching Pitfalls and When Not to Batch

### Head-of-Line Blocking

```
Batch of 100 requests — request 1 is slow:
  [req1 slow] [req2] [req3] ... [req100]
   ↑── takes 500ms

All 100 requests wait for req1 → median latency = 500ms
  Without batching: 99 requests complete in 1ms, 1 in 500ms
  With batching: all 100 requests take 500ms!
```

### Batch Size Tuning

```
Too small → not enough amortization, overhead dominates
Too large → head-of-line blocking, memory pressure, latency spikes

Optimal batch size: benchmark-driven, typically:
  Kafka:     batch.size = 16KB–1MB  (depends on message rate)
  DynamoDB:  BatchWriteItem = max 25 items
  Redis:     Pipeline up to 1,000 commands
  PostgreSQL: COPY for bulk inserts vs INSERT for small counts
```

---

## Summary Table

| Pattern                | What it Exploits         | Trade-off |
|------------------------|--------------------------|-----------|
| CPU Cache (L1/L2/L3)   | Temporal locality        | Cache size limits |
| Sequential I/O         | Spatial locality         | Must scan, not random access |
| In-process cache       | Temporal + computational | Stale data risk |
| Read replicas          | Geographic locality      | Eventual consistency |
| CDN                    | Geographic + temporal    | Cache invalidation complexity |
| Sharding by tenant     | Computational locality   | Cross-tenant queries expensive |
| Batching               | Amortize fixed overhead  | Increased per-request latency |
| Pushdown (MapReduce)   | Compute-at-data          | Latency (batch processing) |
| Denormalization        | Read locality            | Write amplification |
