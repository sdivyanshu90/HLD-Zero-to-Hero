# LSM Trees (Log-Structured Merge Trees)

## The Problem LSM Solves

B-trees require random writes (update page in-place). Random writes are expensive:
- HDD: ~10ms per random write (seek time)  
- SSD: 100µs but causes wear and has limited IOPS

LSM trees convert random writes into sequential writes by always appending, then reorganizing (merging) in the background.

---

## LSM Tree Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      LSM TREE ARCHITECTURE                          │
│                                                                      │
│  WRITE PATH:                                                         │
│                                                                      │
│  Write → ┌──────────┐  Flush when full  ┌──────────────────────┐   │
│           │MemTable  │ ─────────────────▶│  L0 SSTables (disk) │   │
│           │(in RAM,  │                   │  (sorted, immutable) │   │
│           │ sorted   │                   └──────────────────────┘   │
│           │ skip list│                             │ Compact         │
│           └──────────┘                             ▼                │
│                                          ┌──────────────────────┐   │
│  WAL (durability):                       │  L1 SSTables (disk) │   │
│  Write → append to WAL → ACK client      │  (larger, merged)   │   │
│          (sequential → very fast)        └──────────────────────┘   │
│                                                     │ Compact        │
│                                                     ▼               │
│                                          ┌──────────────────────┐   │
│                                          │  L2 SSTables (disk) │   │
│  READ PATH:                              │  (even larger)      │   │
│  Read → Check MemTable (RAM)             └──────────────────────┘   │
│       → Check L0 SSTables               ...                         │
│       → Check L1 → L2 → ...  (bloom filters skip most levels)      │
└────────────────────────────────────────────────────────────────────┘
```

---

## Write Path Deep Dive

### Step 1: WAL Append

```
Client write: SET user:1234 = {name: "Alice", score: 100}

1. Append to WAL (Write-Ahead Log):
   WAL file: [...previous entries..., {user:1234, {name:Alice, score:100}, ts:1000}]
   fsync() → durability guaranteed

2. Insert into MemTable (sorted in-memory structure, typically a skip list):
   MemTable: {user:1000: ..., user:1200: ..., user:1234: {name:Alice, score:100}, user:1500: ...}

3. Return success to client
   Time: ~100µs (WAL write is sequential, MemTable is in-RAM)
```

### Step 2: MemTable Flush

```
When MemTable reaches threshold (typically 64-512 MB):
  1. Freeze current MemTable (it becomes immutable)
  2. Create new empty MemTable for incoming writes
  3. Flush frozen MemTable to disk as L0 SSTable (Sorted String Table)

SSTable format:
  ┌─────────────────────────────────────────────────┐
  │  Data blocks (sorted key-value pairs):          │
  │  [user:1000: ...] [user:1200: ...] [user:1234: ...]│
  ├─────────────────────────────────────────────────┤
  │  Index block (sparse index of every N-th key):  │
  │  [user:1000 → offset:0] [user:1200 → offset:4KB]│
  ├─────────────────────────────────────────────────┤
  │  Bloom filter (bit array for fast negative lookup)│
  │  [is user:1234 in this file? 95% certain yes]   │
  ├─────────────────────────────────────────────────┤
  │  Footer (block offsets, magic number)           │
  └─────────────────────────────────────────────────┘
```

---

## Compaction

L0 accumulates many SSTable files (which may have overlapping key ranges). Compaction merges them into larger, non-overlapping SSTables at lower levels:

```
Before compaction (L0 — overlapping key ranges):
  L0 file 1: [A...M]  (newest)
  L0 file 2: [C...R]
  L0 file 3: [B...Z]  (oldest)

After compaction to L1 (merged, sorted, non-overlapping):
  L1 file 1: [A...H]
  L1 file 2: [I...R]
  L1 file 3: [S...Z]

Compaction process:
  1. Multi-way merge sort of overlapping files
  2. For duplicate keys: keep newest version (by timestamp/sequence number)
  3. Mark deleted keys (tombstones) for eventual removal
  4. Write merged output to new, larger SSTable
  5. Delete old input SSTables
```

### Leveled Compaction (RocksDB/LevelDB default)

```
Level   Max Size    Max Files   Key Range
──────────────────────────────────────────────────
L0      ~256 MB     4-8 files   Overlapping (just flushed from MemTable)
L1      256 MB      10 files    Non-overlapping (single key space)
L2      2.5 GB      100 files   Non-overlapping
L3      25 GB       1000 files  Non-overlapping
L4      250 GB      ...
...

Size ratio: 10× per level
Each level is kept sorted and non-overlapping
→ Reads at most touch 1 file per level (except L0)
→ Space amplification: ~1.1× (only ~10% overhead)
→ Write amplification: 10-30× (keys rewritten at each compaction)
```

### STCS: Size-Tiered Compaction (Cassandra default)

```
Groups SSTables of similar size and merges them when N reach a threshold:

  4 small tables → merge → 1 medium table
  4 medium tables → merge → 1 large table
  4 large tables → merge → 1 very large table

Pros: Lower write amplification (keys written fewer times)
Cons: Higher space amplification (multiple copies of same key in different tiers)
      Reads may need to check many files (no level guarantee)
```

---

## Read Path with Bloom Filters

Without bloom filters, every SSTable on every level must be checked on every read:

```
Naive read for user:1234:
  Check MemTable: not found
  Check L0 file 1: read → not found (1 disk read!)
  Check L0 file 2: read → not found (1 disk read!)
  Check L0 file 3: read → not found (1 disk read!)
  Check L1 file 1: read → not found (1 disk read!)
  ...
  Check L3 file 47: read → FOUND!    (1 disk read!)
  Total: many disk reads for a single key!

With Bloom filters:
  Check MemTable: not found
  Check L0 file 1 bloom filter: "definitely NOT here" → skip (0 disk reads!)
  Check L0 file 2 bloom filter: "might be here" → read → found!
  Total: 1 bloom filter check (in RAM) per file, 1 disk read at most

Bloom filter trade-off:
  False positive rate: 1% (1% of "might be here" responses are wrong)
  Memory: ~10 bits per key
  For 1B keys: 10 Gb / 8 = 1.25 GB RAM → acceptable
```

---

## LSM vs B-Tree Performance Summary

```
Metric              B-Tree            LSM Tree
──────────────────────────────────────────────────────────
Write throughput    Moderate          Very high (sequential)
Write latency       Low (in-place)    Very low (WAL + MemTable)
Write amplification 5-10×             10-30× (leveled), 3-10× (tiered)
Read latency        Low (B-tree walk) Medium (check multiple levels)
Read amplification  Low               Medium (bloom filter helps)
Space amplification Low               Low (leveled), Medium (tiered)
Range scan          Excellent         Good (sorted SSTables)
Compaction I/O      Background VACUUM Background merge
Used by             PostgreSQL, MySQL  Cassandra, RocksDB, LevelDB, HBase, BigTable
```

---

## Interview Quick Answers

- **Why does Cassandra use an LSM tree instead of a B-tree?** — Cassandra is write-optimized. LSM converts all writes to sequential appends (fast on any storage), while B-trees require random writes (expensive IOPS on HDD, SSD wear). Cassandra trades slightly higher read latency for dramatically higher write throughput.
- **How does an LSM tree achieve durability?** — WAL (Write-Ahead Log): every write is appended to a sequential WAL and fsynced before the client ACK. If the process crashes, the WAL is replayed to reconstruct the MemTable.
- **What is a tombstone in an LSM tree?** — A delete marker. Because SSTables are immutable, you can't remove a key in-place. Instead, a tombstone record is written. During compaction, tombstones cause old versions to be dropped. If compaction hasn't run, tombstones accumulate → "tombstone issue" in Cassandra.
