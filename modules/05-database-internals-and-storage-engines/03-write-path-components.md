# Write Path Components: WAL, MemTable, Buffer Pool

## The Critical Insight: Writing to Disk is Expensive

Random disk writes are the bottleneck for database performance:
- HDD: 10ms per seek = 100 IOPS max
- NVMe SSD: 100µs per random write = 10,000 IOPS max
- Sequential write: 500MB/s+ → millions of sequential write ops/s

Every database uses some combination of in-memory buffering and sequential logging to convert expensive random writes into cheap sequential writes.

---

## Write-Ahead Log (WAL)

The WAL is an append-only sequential log of every database modification. It is the primary mechanism for durability and crash recovery.

```
WAL File Structure (PostgreSQL):
  ┌─────────────────────────────────────────────────────────────┐
  │  WAL Segment (16MB default per file)                        │
  │  ┌────────────────────────────────────────────────────────┐ │
  │  │  Record 1: XID=100, INSERT users(1, 'Alice', 'a@..')   │ │
  │  │  Record 2: XID=100, INSERT orders(1, 1, 50.00)         │ │
  │  │  Record 3: XID=100, COMMIT                              │ │
  │  │  Record 4: XID=101, UPDATE users SET name='Bob' ...     │ │
  │  │  Record 5: XID=101, COMMIT                              │ │
  │  │  ...                                                    │ │
  │  └────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────┘

Each record contains:
  - Transaction ID (XID)
  - Type of operation (INSERT/UPDATE/DELETE)
  - Table OID (which table)
  - Old/new row values (or delta)
  - CRC32 checksum
```

### WAL Write Protocol

```
Client transaction:
  BEGIN;
  INSERT INTO orders ...;
  INSERT INTO order_items ...;
  COMMIT;

WAL write sequence:
  1. INSERT: write WAL record for first row (RAM buffer, not disk yet)
  2. INSERT: write WAL record for second row (RAM buffer)
  3. COMMIT: 
     a. Write COMMIT record to WAL buffer
     b. fsync() WAL buffer to disk  ← THE KEY DURABILITY POINT
     c. Return success to client
  4. Background: apply changes to data pages (heap files)

Key insight: the fsync of the WAL is what makes the transaction durable.
  The data pages can be written asynchronously AFTER the client ACK.
```

### WAL and Recovery

```
Crash at step 4 (WAL committed, data pages not fully written):
  On restart: scan WAL from last checkpoint
  Find all committed transactions → redo their changes to data pages
  Find uncommitted transactions → rollback (undo incomplete changes)

  This guarantees: committed transactions survive any crash
                   uncommitted transactions leave no trace
```

---

## Group Commit (Throughput Optimization)

fsync is expensive (~1-5ms). Group commit batches multiple transactions' WAL records into one fsync:

```
Without group commit:
  Transaction 1 commit → fsync → 5ms → return to client
  Transaction 2 commit → fsync → 5ms → return to client
  Transaction 3 commit → fsync → 5ms → return to client
  Max throughput: 200 TPS

With group commit:
  Transaction 1 commit → wait for group ...
  Transaction 2 commit → wait for group ...
  Transaction 3 commit → all 3 together → ONE fsync → 5ms → return all 3
  Max throughput: 3 × 200 = 600 TPS (with 3-way grouping)
  At 10,000 concurrent clients: potentially 10,000 commits per fsync

PostgreSQL: commit_delay + commit_siblings parameters
MySQL InnoDB: innodb_flush_log_at_trx_commit=2 (relaxed durability) or =1 (strict)
Kafka: acks=all, controlled by producer batch.linger.ms
```

---

## Buffer Pool (PostgreSQL) / InnoDB Buffer Pool

The buffer pool is the database's page cache: hot disk pages kept in RAM to avoid repeated I/O.

```
┌─────────────────────────────────────────────────────────────────┐
│                     BUFFER POOL ARCHITECTURE                     │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  BUFFER POOL (e.g., 64 GB)                │  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│  │  │ Page 1  │  │ Page 2  │  │ Page 3  │  │ Page N  │   │  │
│  │  │ (dirty) │  │ (clean) │  │ (dirty) │  │ (clean) │   │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│  │                                                           │  │
│  │  Page table: page_id → buffer frame mapping               │  │
│  │  LRU list:  least recently used → evict first             │  │
│  │  Dirty list: pages modified but not yet flushed to disk   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                        │
│                   Background writer                              │
│                   flushes dirty pages                            │
│                          │                                        │
│                       Storage (SSD/HDD)                          │
└─────────────────────────────────────────────────────────────────┘
```

### Buffer Pool Hit Rate

```
Buffer pool hit rate = reads served from RAM / total reads

At 99% hit rate:
  1,000 reads: 990 from RAM (0µs), 10 from SSD (100µs each)
  Average read time: (990 × 0 + 10 × 100) / 1,000 = 1µs

At 90% hit rate:
  1,000 reads: 900 from RAM, 100 from SSD
  Average read time: (900 × 0 + 100 × 100) / 1,000 = 10µs

At 50% hit rate:
  Average read time: 50µs (severe degradation!)

Rule of thumb: buffer pool should be large enough to hold your working set
  Working set: all pages accessed in a typical query window
  Monitor: pg_stat_bgwriter (PostgreSQL), SHOW ENGINE INNODB STATUS (MySQL)
```

### Dirty Page Flushing

```
Dirty pages must be flushed to disk eventually:
  1. Checkpoint: periodically write all dirty pages → ensure recovery is fast
     PostgreSQL checkpoint_timeout = 5min (don't let WAL grow too large)
  2. LRU eviction: when buffer pool is full, evict dirty pages first (flush then evict)
  3. Background writer: proactively writes dirty pages in low-activity periods

  Background writer parameters (PostgreSQL):
    bgwriter_delay = 200ms (wake up frequency)
    bgwriter_lru_maxpages = 100 (max pages to flush per cycle)
    bgwriter_lru_multiplier = 2.0 (how aggressively to clean ahead)
```

---

## MemTable (LSM Systems)

In LSM-based databases (RocksDB, Cassandra, LevelDB), the MemTable is the in-memory write buffer:

```
MemTable:
  - Sorted in-memory structure (skip list in RocksDB, sorted hash in Cassandra)
  - All writes go here first (after WAL)
  - Reads check here before checking SSTables
  - When full (e.g., 64 MB): flush to L0 SSTable on disk

Skip List (RocksDB MemTable):
  Level 3: 1 ─────────────────────────────────────── 10
  Level 2: 1 ──────── 4 ──────────────── 8 ────────── 10
  Level 1: 1 ── 2 ─── 4 ── 5 ─── 7 ─── 8 ── 9 ────── 10
  Level 0: 1 ─ 2 ─ 3 ─ 4 ─ 5 ─ 6 ─ 7 ─ 8 ─ 9 ─ 10

  Skip list achieves O(log N) search, insert, delete
  Concurrent writes: optimistic locking per skip list node
```

---

## The Write Pipeline: Putting It All Together

```
Write journey in RocksDB/Cassandra:

Client write: PUT key=user:1234 value={...}
    │
    ▼
1. WAL append (sequential write to append-only file) ── fast, durable
    │
    ▼
2. MemTable insert (sorted in-memory skip list) ── fast, in RAM
    │
    ▼
3. ACK to client ── sub-millisecond!
    │
    (background)
    ▼
4. MemTable reaches 64 MB threshold
    │
    ▼
5. Flush to L0 SSTable (immutable sorted file on disk)
    │
    (background)
    ▼
6. L0 reaches 4-8 files → trigger compaction
    │
    ▼
7. Multi-way merge into L1 SSTables (sequential write, efficient)
    │
    (continues)
    ▼
8. Eventually data settles in Lmax (infrequently accessed cold data)
```

---

## Interview Quick Answers

- **What is the WAL and why is it needed?** — Write-Ahead Log: an append-only sequential log of all modifications. fsync'ing the WAL before acknowledging a write gives durability. On crash, the WAL is replayed to recover committed changes. Without WAL, durability requires writing data pages immediately (slow random I/O).
- **Why is the buffer pool important for DB performance?** — It keeps hot pages in RAM, converting random disk reads into RAM accesses (100ns vs 100µs = 1000× faster). Buffer pool hit rate should be >99% for good performance.
- **What is group commit?** — Batching multiple transactions' WAL flush into a single fsync. Reduces the number of expensive fsync calls, increasing transaction throughput significantly under load.
