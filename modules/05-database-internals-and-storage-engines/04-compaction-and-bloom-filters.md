# Compaction and Bloom Filters

## The Compaction Problem

LSM trees accumulate many SSTable files over time. Without compaction:
1. **Read amplification**: every read must check all SSTable files at every level
2. **Space amplification**: old, superseded versions of keys remain on disk
3. **Tombstone accumulation**: deleted keys' tombstones never get garbage collected

Compaction merges and reorganizes SSTables to control these problems.

---

## Compaction Strategies

### Size-Tiered Compaction Strategy (STCS)

Cassandra's default strategy for write-heavy workloads:

```
STCS Algorithm:
  1. SSTable files are grouped by size
  2. When a group reaches N files (default: 4), merge them

  Evolution of a key over time:
  ┌────────────────────────────────────────────────────────────────┐
  │  Time:  1     2     3     4     5     6     7     8           │
  │                                                                │
  │  L0:   [s1]  [s2]  [s3]  [s4]                                │
  │              ↓ 4 small SSTables → merge                       │
  │  L1:         [──── M1 ────]  [s5]  [s6]  [s7]  [s8]         │
  │                              ↓ 4 medium SSTables → merge      │
  │  L2:                         [──────── M2 ────────]           │
  └────────────────────────────────────────────────────────────────┘

Write amplification: ~10× (each key written ~10 times across all levels)
Space amplification: ~2× (two copies of overlapping data exist during compaction)
Read amplification: Can be high (many files to check per level)

Use STCS when: write throughput is the priority (time-series, append-heavy)
```

### Leveled Compaction Strategy (LCS)

RocksDB's default (and Cassandra's option for read-heavy):

```
LCS Algorithm:
  1. L0: accepts flushed MemTables (may overlap)
  2. L1+: strict non-overlapping key ranges per level
  3. When Ln is full: pick one SSTable, merge with overlapping Ln+1 SSTables

  Key guarantee: a given key exists in at most ONE SSTable per level ≥ L1
  → Reading a key touches at most 1 file per level (+ L0)
  → Predictable read performance

  L0: 4 files    → trigger compaction to L1
  L1: max 256 MB → trigger compaction to L2 when exceeded
  L2: max 2.5 GB  → 10× ratio per level
  L3: max 25 GB

Write amplification: ~30× (level size ratio 10×, amortized over levels)
Space amplification: ~1.1× (very low — data at each level is compact)
Read amplification: Very low (1 file per level + L0)

Use LCS when: read latency is the priority (OLTP, mixed workloads)
```

### TWCS: Time-Window Compaction Strategy

Cassandra optimization for pure time-series data with TTL:

```
TWCS:
  Groups SSTables by the time window they were written
  Compacts within each time window
  When a window's TTL expires: delete entire SSTable files cheaply

  Day 1 SSTables → [compacted into 1 Day-1 file]
  Day 2 SSTables → [compacted into 1 Day-2 file]
  ...
  After 7 days: delete Day-1 file entirely (no per-row deletion needed!)

Best for: IoT sensor data, logs, metrics — data with natural expiry
```

---

## Compaction Impact on Read/Write Performance

```
During compaction:
  - Significant disk I/O for reading old SSTables and writing new ones
  - Can consume 50-80% of disk bandwidth
  - Causes read latency spikes if compaction is behind

Compaction debt:
  If writes arrive faster than compaction can keep up:
    L0 accumulates 20, 30, 40 files...
    Each read must scan all L0 files!
    Read latency degrades severely

Cassandra compaction starvation:
  Default: 32 compaction threads
  If compaction is behind: "Compaction is 8,000 SSTables behind"
  Fix: reduce write rate, increase compaction threads, better hardware
```

---

## Bloom Filters: Avoiding Unnecessary Disk Reads

A Bloom filter is a space-efficient probabilistic data structure that answers: **"Is this key definitely NOT in this SSTable?"**

### How Bloom Filters Work

```
Bloom filter for a set S = {user:100, user:200, user:300}:

Bit array:  [0][0][1][0][1][0][1][1][0][0]
              0  1  2  3  4  5  6  7  8  9

Insert user:100:
  Hash1(user:100) % 10 = 2 → set bit 2
  Hash2(user:100) % 10 = 4 → set bit 4
  Hash3(user:100) % 10 = 6 → set bit 6

Insert user:200:
  Hash1(user:200) % 10 = 7 → set bit 7
  Hash2(user:200) % 10 = 3 → set bit 3
  Hash3(user:200) % 10 = 2 → bit 2 already set

Query user:1234:
  Hash1(user:1234) % 10 = 5 → bit 5 = 0 → DEFINITELY NOT HERE! (no disk read)

Query user:999:
  Hash1(user:999) % 10 = 2 → bit 2 = 1
  Hash2(user:999) % 10 = 4 → bit 4 = 1
  Hash3(user:999) % 10 = 7 → bit 7 = 1
  → All bits set → MIGHT BE HERE → do a disk read
  → (user:999 is not actually there → false positive, wasted 1 disk read)
```

### Bloom Filter Properties

```
False positive rate (probability of "might be here" when key is absent):
  p ≈ (1 - e^(-kn/m))^k

  k = number of hash functions
  n = number of elements
  m = number of bits

  Optimal k = (m/n) × ln(2)

  For 1% false positive rate:
    m/n ≈ 9.6 bits per element
    k ≈ 6.7 hash functions (round to 7)

  For 0.1% false positive rate:
    m/n ≈ 14.4 bits per element
    k ≈ 10 hash functions

Memory cost:
  1B keys × 10 bits = 10Gb / 8 = 1.25 GB RAM for 1% FPR
  This is the standard trade-off: pay ~1-2 GB RAM, save millions of disk reads
```

### Bloom Filter Trade-offs

```
✓ No false negatives: "definitely NOT here" is always accurate
✗ False positives: ~1% chance of "might be here" being wrong → wasted disk read
✗ Cannot delete elements (deleting would require knowing which bits to unset,
    but bits may be shared with other elements)
    → Counting Bloom filters support deletion (at 2-4× memory cost)
✓ O(k) time for both insert and query (k hash computations, constant per k)
✓ Not affected by number of elements (no pointer chasing, no hash table collisions)
```

---

## Other Probabilistic Data Structures in Databases

### HyperLogLog (Cardinality Estimation)

```
Problem: COUNT(DISTINCT user_id) in a 1B row table requires storing all seen IDs

HyperLogLog:
  Uses ~12 KB of memory regardless of dataset size
  Estimates distinct count with 0.81% standard error

  SELECT approx_count_distinct(user_id) FROM events;
  → Returns ~500,000,000 ± 0.81% with 12KB memory
  vs
  SELECT COUNT(DISTINCT user_id) FROM events;
  → Requires 500M entries in a hash table → 4 GB memory

Used by: Redis PFCOUNT, PostgreSQL hll extension, BigQuery APPROX_COUNT_DISTINCT
```

### Count-Min Sketch (Frequency Estimation)

```
Problem: find top-K most frequent keys in a stream without storing all counts

Count-Min Sketch:
  2D array of counters, multiple hash functions
  Update: increment counter at (hash1(key) % w), (hash2(key) % w), ...
  Query: return min of all counter positions for a key

  Overestimates frequency (adds noise from hash collisions)
  Underestimates: never
  Memory: fixed size, independent of number of distinct keys

Used by: network traffic analysis, Redis Heavy Hitters, Flink frequency estimation
```

---

## Interview Quick Answers

- **What is compaction and why is it necessary in LSM trees?** — Compaction merges overlapping SSTables, removes stale versions of keys, and drops tombstones. Without it, read performance degrades (too many files to check), space amplification grows, and tombstones accumulate causing "zombie" data.
- **What is a bloom filter and why do LSM databases use it?** — A probabilistic data structure that answers "is key X in this SSTable?" with no false negatives. Before doing an expensive SSTable disk read, the bloom filter is checked. If it says "definitely not here," the disk read is skipped. Reduces read amplification from O(levels) to O(1) for most reads.
- **Can you delete items from a bloom filter?** — Not in standard Bloom filters (bit-sharing prevents safe deletion). Counting Bloom filters support deletion at 2-4× memory cost. For LSM databases, deletions use tombstones that are cleaned up during compaction instead.
