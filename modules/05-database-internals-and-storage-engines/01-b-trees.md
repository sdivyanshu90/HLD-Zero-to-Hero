# B-Trees and B+ Trees

## Why Storage Engines Matter

The data structure a database uses to organize data on disk fundamentally determines its read vs write performance, memory efficiency, and suitability for different workloads.

---

## B-Tree: The Dominant Read-Optimized Structure

A B-tree is a self-balancing tree data structure that maintains sorted data and allows efficient search, sequential access, insertions, and deletions. Every major RDBMS index is a B-tree (or B+ tree variant).

```
B+ Tree (most common variant):

                    ┌─────────────┐
                    │  30  │  70  │     ← Internal node (keys only)
                    └──┬───┴───┬──┘
           ┌───────────┘       └───────────┐
    ┌──────┴──────┐             ┌──────────┴──────┐
    │  10  │  20  │             │  50  │  60  │   │   ← Internal nodes
    └──┬───┴──┬───┘             └──┬───┴──┬───┘
  ┌────┘    ┌─┘               ┌───┘    ┌──┘
  ▼         ▼                 ▼        ▼
[1,5,8] → [10,15] → [20,25] → [30,40,50] → [60,65] → [70,80,90]
  ↑── Leaf nodes: contain actual data (or pointers to data pages)
  ↑── Linked list for efficient range scans: → → →
```

### Key Properties

```
B+ Tree properties:
  - All actual data is in leaf nodes (internal nodes are just routing keys)
  - Leaf nodes are linked together for O(N) sequential scan
  - All paths from root to leaf have the same depth (balanced)
  - Each node holds between ⌈m/2⌉ and m-1 keys (m = order)

Height for 1 billion rows (m=100 keys/node):
  log_100(1,000,000,000) ≈ 4.5 levels

  Only 5 disk reads to find any row in a 1B-row table!
  (Compare to linear scan: 1,000,000,000 reads worst case)
```

---

## B-Tree Node Structure on Disk

```
Disk page (4KB or 8KB — aligns to OS page size):

┌──────────────────────────────────────────────────────────────┐
│  Page Header (20 bytes)                                       │
│  ┌──────────┬──────────┬──────────┬────────────────────────┐ │
│  │ page_id  │  is_leaf │  n_keys  │  checksum              │ │
│  └──────────┴──────────┴──────────┴────────────────────────┘ │
│                                                               │
│  Keys (each key: variable size, e.g., 8 bytes for int64):   │
│  [ key_1 | key_2 | key_3 | ... | key_N ]                    │
│                                                               │
│  Child pointers (N+1 pointers for internal node):            │
│  [ ptr_0 | ptr_1 | ptr_2 | ... | ptr_N ]                    │
│                                                               │
│  Values (leaf only — row data or heap pointer):              │
│  [ val_1 | val_2 | val_3 | ... | val_N ]                    │
└──────────────────────────────────────────────────────────────┘
```

For a 4KB page with 8-byte keys and 8-byte pointers:
- Each internal node holds ~250 keys → tree stays very shallow

---

## Read Performance

```
Finding a single row by primary key:
  1. Load root node from disk    (1 I/O)
  2. Binary search within node → follow pointer
  3. Load level-2 node           (1 I/O)
  4. Binary search → follow pointer
  5. Load level-3 node           (1 I/O)
  6. Binary search → found leaf pointer
  7. Load leaf node              (1 I/O)
  8. Return data row

Total: ~4 I/Os for 1B-row table (typical 3-5 I/Os for most real tables)
With buffer pool (hot pages cached in RAM): often 0-2 I/Os

Range scan:
  SELECT * FROM orders WHERE created_at BETWEEN '2024-01' AND '2024-02';
  1. Find first leaf node for '2024-01' (4 I/Os)
  2. Scan linked leaf list sequentially → very cache-friendly
  → Excellent range scan performance
```

---

## Write Performance

```
Inserting a new key:
  1. Find the correct leaf node     (4 I/Os read)
  2. Insert key into sorted position in leaf
  3. If leaf is full:
     a. Split leaf: half keys go to new leaf node (1 disk write)
     b. Promote middle key to parent (1 disk write)
     c. If parent also full → cascade splits up the tree
  4. Write-ahead log (WAL) fsync   (1 I/O)
  5. Write modified pages          (1-4 I/Os)

Worst case: cascading splits to root → O(h) writes (h = tree height)
In practice: splits are rare; most inserts modify only one leaf
```

### Write Amplification

```
B-Tree write amplification:
  1 logical write (new row) → multiple physical disk writes:
    - WAL entry
    - Modified page (possibly multiple on split)
    - Index pages (one per index on the table)

  Table with 5 indexes:
    1 INSERT = 1 WAL + 6 data/index page writes = ~7 I/Os

  At 100K inserts/s: 700K random disk writes/s
  NVMe SSD: 500K IOPS max → BOTTLENECK!
```

---

## B-Tree vs Alternatives: When to Use

```
B-Tree strengths:
  ✓ Fast point reads (O(log N) — a few disk I/Os)
  ✓ Efficient range scans (linked leaf list)
  ✓ Updates in-place (no separate compaction needed)
  ✓ Predictable read latency

B-Tree weaknesses:
  ✗ Write amplification (random I/O on insert/update/delete)
  ✗ Fragmentation over time (space left by deleted rows)
  ✗ Random writes hurt SSD wear and IOPS budget
  ✗ Must take page locks under high concurrency (write contention)
```

```
Use B-Tree (RDBMS) when:
  - Read-heavy workloads (OLTP with mostly reads)
  - Frequent range queries (time ranges, sorted pagination)
  - Strong ACID guarantees needed (PostgreSQL, MySQL)
  - Update-in-place semantics needed

Use LSM Tree (NoSQL) when:
  - Write-heavy workloads (time-series, event logs, messaging)
  - Append-mostly patterns (new data rarely updates old data)
  - Sequential write throughput matters
```

---

## Practical Examples

```
PostgreSQL btree index:
  CREATE INDEX idx_orders_customer ON orders(customer_id);
  → B+ Tree index on customer_id
  → SELECT * FROM orders WHERE customer_id = 123 → 4 I/Os vs full scan

  CREATE INDEX idx_orders_range ON orders(created_at);
  → Range query: WHERE created_at > '2024-01' → linked leaf scan

  B-Tree internal data: stored in 8KB pages
  Default fill factor: 100% (100% pages packed on initial creation)
  Insert fill factor: 70-80% (leaves space to avoid splits on insert)
```

---

## Interview Quick Answers

- **Why is a B+ tree preferred over a binary search tree for databases?** — A binary tree with 1B elements has height ~30 (log2(1B)), meaning 30 disk I/Os per lookup. A B+ tree with 1B elements and 250 keys/node has height ~5 (log250(1B)), meaning ~5 disk I/Os. Each node fits in one disk page → massive I/O reduction.
- **How does a database range scan work on a B-tree index?** — Find the first matching leaf node (log N traversal), then follow the linked list of leaf nodes sequentially until the range end. Sequential reads are fast and prefetchable.
- **What is write amplification in a B-Tree?** — One logical write causes multiple physical disk writes: WAL, modified data pages, modified index pages. Can be 5-10× amplification for tables with multiple indexes.
