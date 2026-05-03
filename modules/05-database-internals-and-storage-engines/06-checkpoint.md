# Module 05 Checkpoint: Database Internals and Storage Engines

## Questions to Test Your Understanding

---

**Q1.** A table has 1 billion rows. How many disk I/Os does a B-tree primary key lookup require?

> **Answer:** About **4-5 disk I/Os**. With 250 keys per 8KB node, height = log₂₅₀(1B) ≈ 4.5 levels ≈ 5 levels. With a warm buffer pool caching the root and upper levels, this often reduces to 2-3 actual disk I/Os in practice.

---

**Q2.** A Cassandra node crashes before flushing its MemTable. Is data lost?

> **Answer:** No. The WAL (CommitLog in Cassandra) was fsynced before the write was acknowledged. On restart, Cassandra replays the CommitLog to reconstruct the MemTable. Data committed before the crash is recovered. Any write where the CommitLog fsync hadn't completed would correctly not appear.

---

**Q3.** Why does a bloom filter have no false negatives but can have false positives?

> **Answer:** A bloom filter can only set bits, never unset them. When a key is added, its corresponding bits are set. When querying, if ANY bit is 0 → the key is definitely absent (no false negative possible — adding the key would have set all its bits). If all bits are 1 → the key might be present OR other keys happened to set those same bits (false positive). The probability is tunable by adjusting bit array size and number of hash functions.

---

**Q4.** You have a service writing 500,000 events/second. What storage engine and compaction strategy do you recommend?

> **Answer:** LSM Tree (Cassandra or RocksDB) with Time-Window Compaction Strategy (TWCS) if data has natural time ordering and TTL. Reasons: LSM converts random writes to sequential appends. TWCS groups SSTables by time window — when a window's TTL expires, the entire SSTable is deleted cheaply (no per-row tombstone processing). For 500K events/s at 100 bytes each = 50 MB/s — well within Cassandra's capacity on NVMe hardware.

---

**Q5.** Compare read amplification of LCS vs STCS.

> **Answer:**
> - **LCS (Leveled)**: At most 1 file per level is checked per read (L0 is an exception). For a 5-level tree, a read checks at most 1 file in L0 + 1 per level = ~5 files. Bloom filters reduce further.
> - **STCS (Tiered)**: Files within a tier can have overlapping key ranges. A read may check all N files in a tier. With 4 tiers of 4 files each = 16 files in the worst case.
> - Conclusion: LCS provides more predictable, lower read amplification at the cost of higher write amplification.

---

## Checklist

- [ ] B+ Tree: all data in leaves, linked for range scans, height = log_m(N) ≈ 4-5 I/Os for 1B rows
- [ ] B-Tree writes: WAL first, then in-place page modification
- [ ] LSM write path: WAL → MemTable → flush to L0 SSTable → compact to L1...
- [ ] LSM compaction: STCS (write-optimized), LCS (read-optimized), TWCS (time-series)
- [ ] Bloom filter: no false negatives, ~1% false positives, ~10 bits/key
- [ ] Buffer pool: keeps hot pages in RAM, hit rate should be >99%
- [ ] Group commit: batches multiple transaction fsyncs into one
- [ ] Columnar: 5-25× less I/O for analytical aggregates; better compression
- [ ] WAL: durability mechanism; fsync before ACK; replayed on crash recovery
