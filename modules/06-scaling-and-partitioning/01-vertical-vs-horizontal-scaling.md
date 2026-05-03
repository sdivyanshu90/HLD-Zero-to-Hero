# Vertical vs Horizontal Scaling

## The Fundamental Trade-off

When a system outgrows its current capacity, there are exactly two strategies:

```
Vertical Scaling (Scale Up):            Horizontal Scaling (Scale Out):
  Replace with bigger machine             Add more machines

  ┌─────────────┐                        ┌────┐ ┌────┐ ┌────┐
  │             │                        │ S1 │ │ S2 │ │ S3 │
  │  8-core     │  →   ┌─────────────┐  └────┘ └────┘ └────┘
  │  32 GB RAM  │      │  64-core    │    ┌────┐ ┌────┐ ┌────┐
  │  1 TB SSD   │      │  512 GB RAM │    │ S4 │ │ S5 │ │ S6 │
  │             │      │  10 TB NVMe │    └────┘ └────┘ └────┘
  └─────────────┘      └─────────────┘
```

---

## Vertical Scaling Deep Dive

```
Advantages:
  ✓ No code changes needed (application unchanged)
  ✓ No distributed systems complexity
  ✓ ACID transactions remain trivially easy
  ✓ Zero latency between components (same machine)
  ✓ Operational simplicity (fewer moving parts)

Disadvantages:
  ✗ Hard ceiling: largest instance type available (e.g., AWS r6i.32xlarge: 128 vCPU, 1 TB RAM)
  ✗ Single point of failure (one big machine = one failure domain)
  ✗ Downtime required to upgrade hardware
  ✗ Cost: exponentially more expensive as you scale up
       4-core machine: $100/month
       8-core machine: $250/month  (not 2×, more like 2.5×)
       64-core machine: $3,000/month (30×!)
  ✗ Cannot exceed physics: memory bandwidth, CPU core speed ceilings

Cost curve:
  vCPUs:  2    4     8     16    32    64    128
  Cost:   1×   2×    5×    12×   30×   80×   200×
  Roughly superlinear — doubling capacity costs more than 2×
```

### When Vertical Scaling Wins

```
Use vertical scaling first:
  1. You don't yet know your access patterns well → avoid premature sharding
  2. Data consistency is paramount (financial transactions)
  3. Complex queries that cross all data (analytics, ad-hoc SQL)
  4. Engineering cost of distributed systems is prohibitive

Rule of thumb: exhaust vertical scaling first
  Single large PostgreSQL instance can handle:
    - 50,000+ queries/second (with proper indexing + buffer pool)
    - 10+ TB of data (with pg_partman table partitioning)
    - Many years of a typical startup's growth
```

---

## Horizontal Scaling Deep Dive

```
Advantages:
  ✓ Theoretically unlimited scale (just add nodes)
  ✓ Fault tolerance (N-1 nodes can fail, system stays up)
  ✓ Geographic distribution (nodes in different datacenters)
  ✓ Cost: commodity hardware is much cheaper per unit than enterprise gear
  ✓ Incremental capacity (add one node at a time)

Disadvantages:
  ✗ Distributed systems complexity (partitioning, replication, consensus)
  ✗ Cross-shard transactions are hard (2PC, Saga patterns)
  ✗ Cross-shard queries are expensive (scatter-gather, fan-out)
  ✗ Operational overhead (cluster management, node failures)
  ✗ Consistency challenges (CAP theorem trade-offs)
```

### The Distributed Systems Tax

```
Single-machine operation:
  SELECT * FROM orders WHERE user_id = 123;
  Cost: B-tree lookup, ~4 I/Os, 1ms

Cross-shard query (user 123 data on Shard 2 of 8):
  1. Identify correct shard: hash(123) % 8 = shard 2
  2. Route query to shard 2
  3. Shard 2 executes query
  4. Return result
  Cost: network RTT (0.5ms) + query (1ms) = 1.5ms (50% overhead)

Scatter-gather query (aggregate across all users):
  SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01';
  1. Fan out query to all 8 shards in parallel
  2. Each shard returns its count
  3. Coordinator sums results
  Cost: max(shard latencies) + coordination overhead
  Operationally complex; shard failures require partial result handling
```

---

## Read Replicas: The Middle Ground

Before horizontal sharding, read replicas can 10× your read capacity:

```
Architecture:
  ┌──────────────┐
  │   Primary    │◄── all writes
  │   (Read +    │
  │    Write)    │
  └──────┬───────┘
         │ async replication
    ┌────┴────────────┐
    ▼                 ▼
┌──────┐          ┌──────┐
│Read  │◄─reads   │Read  │◄─reads
│Repli-│          │Repli-│
│ca 1  │          │ca 2  │
└──────┘          └──────┘

Typical read:write ratio in web applications: 80:20
→ 2 read replicas can handle 3× total throughput (1 primary + 2 replicas)
→ 9 read replicas: 10× read throughput with 0 distributed systems complexity

Cost: replication lag (typically <10ms for same-datacenter async replication)
     Read replicas may return stale data
     Application must know to route time-sensitive reads to primary
```

---

## Scaling Strategy: The Staircase

```
Step 1: Optimize the single node (indexes, query tuning, connection pooling)
  Cost: 0. Effect: often 10-100× improvement before any scaling

Step 2: Add caching layer (Redis/Memcached)
  Cost: 1-2 cache servers. Effect: deflect 80-95% of reads from DB

Step 3: Add read replicas
  Cost: 1-3 replica servers. Effect: scale reads 4-10×

Step 4: Vertical scaling of the primary
  Cost: bigger machine. Effect: more write throughput, more working set in RAM

Step 5: Horizontal sharding
  Cost: significant engineering. Effect: unlimited scale (in theory)
  Only do this when other steps are exhausted!

Most startups never need step 5.
Most unicorns reach step 4-5 after millions of users.
```

---

## Interview Quick Answers

- **When would you choose vertical over horizontal scaling?** — When the engineering complexity of sharding is not worth it: ACID transactions, complex queries, early-stage systems where access patterns aren't known. Start vertical, go horizontal only when you've exhausted vertical options.
- **What is the main challenge with horizontal scaling of databases?** — Cross-shard queries (scatter-gather), cross-shard transactions (distributed 2PC or SAGA), and rebalancing when adding new shards. Sharding also breaks referential integrity across shards.
- **What is the "10× read with read replicas" trick?** — Route read queries to async read replicas. With 9 replicas + 1 primary, you have 10 read paths. Cost: replication lag (usually acceptable for non-time-sensitive reads).
