# Hardware Trade-offs in System Design

## The Core Triangle: Compute, Memory, Storage, Network

Every system design decision is a negotiation across four hardware resources. You cannot optimize all simultaneously — there are always trade-offs:

```
┌─────────────────────────────────────────────────────────────────┐
│                  HARDWARE RESOURCE TRADE-OFF                     │
│                                                                   │
│              COMPUTE                                              │
│             (CPU cycles)                                         │
│                   ▲                                               │
│                  / \                                              │
│                 /   \                                             │
│                /     \                                            │
│               /       \                                           │
│    MEMORY ◄──┼─────────┼──▶ STORAGE                             │
│    (RAM)      \       /     (SSD/HDD)                            │
│                \     /                                            │
│                 \   /                                             │
│                  \ /                                              │
│                   ▼                                               │
│                NETWORK                                            │
│             (bandwidth/latency)                                   │
│                                                                   │
│ Trading one resource for another is valid design.                 │
│ Example: cache (memory) reduces DB load (compute/storage I/O)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Trade-off 1: Memory vs Compute

### Cache Everything (Memory-Heavy)

```
Strategy: precompute and store every possible result in RAM

Example: Twitter home timeline
  Compute-on-read: for each request, compute feed from scratch
    → Query all followees, merge, rank, paginate
    → 100ms+ per request, high DB load

  Memory-heavy: pre-compute and cache every user's timeline in Redis
    → Fanout on write: when @user posts, update all followers' caches
    → 1ms read (cache hit), but huge RAM usage
    → Twitter uses a hybrid (fanout for < 1M followers, compute for celebrities)
```

### Compression (Compute-Heavy, Memory-Light)

```
Strategy: compress data to reduce memory/storage at cost of CPU

Snappy compression:
  Compress: 1 GB → 400 MB in ~500ms  (saves 600 MB memory/disk)
  Decompress: 400 MB → 1 GB in ~200ms on read

Trade-off matrix:
  Compression     CPU cost  Memory/Storage saved  When to use
  None            0         0%                    Hot data, fast access
  Snappy          Low       ~40-60%               Kafka, Cassandra blocks
  LZ4             Very low  ~50%                  Real-time compression
  zstd            Medium    ~60-70%               Columnar stores, cold data
  gzip            High      ~70-80%               HTTP responses, archival
```

---

## Trade-off 2: Disk vs Memory (Durability vs Speed)

```
           Speed     Cost     Durability   Capacity
RAM        100 ns    High     Lost on restart  GBs
NVMe SSD   100 µs   Medium   Persistent   TBs
HDD        10 ms    Low      Persistent   10s TBs

Design choices:
  Redis:        RAM-first, optional persistence (RDB/AOF)
  Memcached:    RAM-only, no persistence
  RocksDB:      NVMe-optimized LSM tree
  PostgreSQL:   Write-ahead log + buffer pool (hybrid)
  Kafka:        Sequential disk writes (effectively as fast as RAM for sequential)
```

### The Write-Ahead Log Pattern

```
Problem: how to be both fast AND durable?

Solution: WAL (Write-Ahead Log)
  1. Append write to sequential log file   → fast (sequential disk = ~500MB/s)
  2. Write to in-memory buffer             → fast (RAM)
  3. Acknowledge to client                 → fast
  4. Background: flush buffer to actual data structures

  On crash: replay WAL to reconstruct memory state
  → Durability: YES (write is on disk before ACK)
  → Speed: YES (sequential append, not random write)

  Used by: PostgreSQL, MySQL InnoDB, RocksDB, Kafka (it IS a WAL)
```

---

## Trade-off 3: Storage Cost vs Query Speed

### Indexing

```
Without index:
  SELECT * FROM orders WHERE customer_id = 1234;
  → Full table scan: read all N rows → O(N)
  → At 1 billion rows: ~10 GB read → ~10 seconds

With B-tree index on customer_id:
  → Navigate tree: O(log N) lookups
  → At 1 billion rows: ~30 comparisons → ~100 µs

Cost: index takes extra storage (~20-30% of table size)
      every INSERT/UPDATE/DELETE must also update the index
```

### Columnar Storage vs Row Storage

```
Row storage (PostgreSQL, MySQL):
  Row 1: [id=1, name="Alice", age=30, email="alice@...", ...]
  Row 2: [id=2, name="Bob",   age=25, email="bob@...",   ...]

  Good for: read entire row (web app fetching one user record)
  Bad for:  aggregate one column across many rows

Columnar storage (Parquet, Redshift, BigQuery):
  id column:    [1, 2, 3, 4, ...]
  name column:  ["Alice", "Bob", "Charlie", ...]
  age column:   [30, 25, 35, ...]

  Good for:  SELECT AVG(age) FROM users  → only reads age column
  Bad for:   SELECT * FROM users WHERE id=1  → reads every column

  SELECT AVG(age) from 1B users:
    Row:      read 1B full rows × 100 bytes  = 100 GB
    Columnar: read 1B ages × 4 bytes         = 4 GB  (25× less I/O)
```

---

## Trade-off 4: Horizontal vs Vertical Scaling

```
Vertical scaling (scale up):
  Single machine: add more RAM, faster CPUs, bigger SSDs
  ✓ No distributed system complexity
  ✓ Strong consistency trivially maintained
  ✗ Single point of failure
  ✗ Cost: diminishing returns (twice the hardware > 2× the price)
  ✗ Hard ceiling: largest cloud instance ~192 vCPUs, 24 TB RAM

Horizontal scaling (scale out):
  Many commodity machines working together
  ✓ Cheaper per unit of capacity
  ✓ Fault tolerant (N-1 machines can fail)
  ✓ No practical ceiling
  ✗ Network overhead between machines
  ✗ CAP theorem: must choose consistency or availability under partition
  ✗ Much more complex to build and operate
```

### When to Choose Each

| Workload | Preferred | Reason |
|----------|-----------|--------|
| Relational OLTP (< 10K req/s) | Vertical | Strong consistency, simpler |
| Analytics / OLAP | Horizontal | Parallelism; data too large for one machine |
| Key-value cache | Horizontal | Linear scaling, simple partitioning |
| Search index | Horizontal | Partition and replicate shard per segment |
| Real-time analytics | Horizontal | Stream partitioning across workers |
| ML training | Vertical + horizontal | GPU clusters, parameter servers |

---

## Trade-off 5: Network Bandwidth vs Latency

```
High-throughput, high-latency scenario:
  Batch job transfers 100 GB across the network
  → Bandwidth: maximize (use large TCP windows, parallel streams)
  → Latency: don't care (batch job runs overnight)

Low-throughput, low-latency scenario:
  HFT trading system sends 100-byte order
  → Bandwidth: irrelevant (tiny messages)
  → Latency: minimize (use kernel bypass RDMA, co-locate with exchange)

Interactive web app:
  → Need low latency AND moderate throughput
  → Use connection pooling, HTTP/2 multiplexing, CDN for static assets
```

---

## Cost Model: Cloud Instance Selection

```
Typical AWS instance families:

c7g (compute-optimized):   High CPU, lower RAM
  → Stateless services, CPU-bound processing

r7i (memory-optimized):    Very high RAM
  → In-memory databases, caches, analytics engines

i4i (storage-optimized):   NVMe SSD, high IOPS
  → Cassandra, Kafka brokers, databases with heavy I/O

p4 (GPU):                  NVIDIA A100 GPUs
  → ML training, inference, video transcoding

g4dn (GPU + compute):      T4 GPUs
  → Inference serving, video processing

Rule of thumb:
  Memory-to-CPU ratio for services:
    Caching:         16-32 GB RAM per 4 vCPUs
    Web servers:     2-4 GB RAM per 4 vCPUs
    Databases:       8-16 GB RAM per 4 vCPUs (buffer pool)
    Kafka brokers:   4-8 GB RAM per 4 vCPUs (OS page cache)
```

---

## Real-World Design Decisions Explained by Hardware

| System | Key Hardware Decision | Why |
|--------|-----------------------|-----|
| Redis | All data in RAM | Sub-millisecond latency impossible with disk |
| Kafka | Sequential disk writes only | Disk sequential ≈ RAM speed; avoids random I/O |
| Cassandra | SSTable on disk + memtable in RAM | LSM tree exploits sequential write speed |
| Elasticsearch | Memory-mapped files | OS manages RAM vs disk automatically |
| ClickHouse | Columnar compression | 10× compression ratio → 10× less I/O |
| Nginx | Async event loop | Avoid thread-per-connection context switch cost |
| gRPC | HTTP/2 multiplexing | One TCP connection, many concurrent streams |
| DynamoDB | SSD-only, no HDD | Consistent low-latency at scale |

---

## Interview Framework for Hardware Trade-offs

When asked about any component, frame your answer in terms of:

1. **What is the dominant cost?** (CPU, memory, I/O, network)
2. **What is the bottleneck you're optimizing for?**
3. **What do you sacrifice to achieve it?**

Example answer: *"For a rate limiter, the dominant cost is latency — each request must check the rate limit before processing. I'd put rate limit counters in Redis (in-memory) to get sub-millisecond checks, sacrificing the memory cost and durability of a database."*
