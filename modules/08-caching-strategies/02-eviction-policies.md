# Cache Eviction Policies

## The Problem: Cache is Full

Caches have limited memory. When full, eviction decides which entries to remove to make room for new ones. The wrong policy leads to thrashing (evicting entries that are immediately needed again) or poor hit rates.

---

## LRU: Least Recently Used

Remove the entry that was least recently accessed:

```
Cache capacity: 3 entries
Access sequence: A, B, C, D, A, B, E, A, B, C, D

State after each access:
  Access A: [A]              hit: -  miss: A
  Access B: [B, A]           hit: -  miss: B
  Access C: [C, B, A]        hit: -  miss: C  (cache full!)
  Access D: [D, C, B]        miss: D, EVICT A  (A was LRU)
  Access A: [A, D, C]        miss: A, EVICT B  (B was LRU)
  Access B: [B, A, D]        miss: B, EVICT C  (C was LRU)
  Access E: [E, B, A]        miss: E, EVICT D  (D was LRU)

Total: 7 misses out of 11 accesses = 36% hit rate

LRU works well when: access pattern is temporal — recently used items
  are likely to be used again soon (most web applications!)
LRU fails when: scanning large datasets (sequential scan evicts all hot cache)
  → "LRU pollution"
```

### LRU Implementation

```
Efficient LRU: doubly-linked list + hash map

Hash map: key → node (O(1) lookup)
Linked list: ordered by recency (head = most recent, tail = LRU)

Access(key):
  node = hashmap[key]
  Move node to head of list
  Return node.value

Evict():
  node = tail of list  ← LRU
  Remove from list and hashmap
  Return

Both operations: O(1) time

Java: LinkedHashMap (access-ordered mode)
Python: OrderedDict (Python 3.7+)
Redis: approximated LRU (not exact, but efficient)
```

---

## LFU: Least Frequently Used

Remove the entry that has been accessed the fewest total times:

```
Cache capacity: 3 entries
Access sequence: A, B, C, A, A, B, D

Counts:
  A: 3 accesses
  B: 2 accesses
  C: 1 access  ← LFU
  D: new entry

  Access D: EVICT C (fewest accesses)

LFU advantages:
  ✓ Keeps truly "popular" items even if not recently accessed
  ✓ Better for workloads with stable frequency distributions

LFU disadvantages:
  ✗ History problem: item accessed 1000× in the past but now cold still survives
  ✗ New items start with count=1 → immediately evicted
  ✗ More complex to implement efficiently: need sorted frequency buckets

Fix for history problem: decay counts over time (move towards LFU-with-decay)
```

---

## ARC: Adaptive Replacement Cache

Automatically adapts between LRU-like and LFU-like behavior:

```
ARC maintains 4 lists:
  T1 (recently seen once): new items go here
  T2 (recently seen twice): items that get a second hit move here
  B1 (ghost for T1): keys of recently evicted T1 items (no data, just keys)
  B2 (ghost for T2): keys of recently evicted T2 items (no data, just keys)

  Target size: p = desired size of T1 (auto-adjusts)
  
  Cache hit in T1: promote to T2 (item was seen twice → more valuable)
  Cache hit in T2: keep at head of T2 (recently frequently used)
  Cache miss, key in B1: increase p (T1 should be larger — recency was underweight)
  Cache miss, key in B2: decrease p (T2 should be larger — frequency was underweight)
  Cache miss, key in neither: add to T1

  ARC adapts to the workload:
    Pure sequential scan: p → 0 (T1 small, items quickly evicted)
    Pure LFU workload: p → 0 (T2 dominates)
    Typical mixed: p settles between 0 and cache_size

Proven: ARC is optimal or near-optimal across a wide range of workloads
Used by: Oracle DB, some filesystem caches, some cloud storage systems
```

---

## TinyLFU: Modern High-Performance Eviction

Used by Caffeine (Java), the current state of the art for in-process caches:

```
TinyLFU = Approximate LFU using Count-Min Sketch + frequency aging

Count-Min Sketch:
  Space-efficient frequency counter (see Module 05)
  Tracks access frequency for ALL items (not just cached ones)
  Space: ~8 bytes per entry regardless of key size

W-TinyLFU (Window-TinyLFU):
  Main cache: protected (LFU, high access frequency items)
  Main cache: probationary (recently evicted from window, being evaluated)
  Window cache: LRU, small (handles new items)
  
  On cache miss:
    Add to window cache (LRU, gives new items a fair chance)
    If window cache full: evict window LRU candidate
    Compare evicted window item's frequency with probationary tail item
    Keep the one with higher frequency
    → Admittance policy: only admit items that are as popular as what they replace

  Advantages:
    ✓ Handles burst access (window cache as landing zone for new items)
    ✓ Efficient memory (Count-Min Sketch, not per-item counters)
    ✓ Frequency decay: periodically halve all counts (forget old history)
    ✓ Excellent real-world performance (beats LRU, LFU, ARC in benchmarks)

  Caffeine benchmark: 30-50% better hit rate than Guava (LRU-based)
                      on real web workloads (Zipfian distribution)
```

---

## TTL (Time-To-Live)

Time-based eviction: entries expire after a fixed duration regardless of access:

```
Redis TTL:
  SET user:1234 "Alice" EX 3600  (expire in 1 hour)
  EXPIRE user:1234 3600
  TTL user:1234 → 3590 (seconds remaining)

When to use TTL:
  ✓ Content that changes over time (user profiles, product prices)
  ✓ Authentication tokens (must expire for security)
  ✓ Session data (clean up inactive sessions automatically)
  ✓ Rate limit windows (expire after window duration)

TTL vs LRU:
  TTL: evicts after fixed time regardless of usage
  LRU: evicts least recently used
  
  Combined: set both TTL and capacity limit
    TTL: ensures stale data eventually expires
    LRU: ensures capacity stays within bounds
    Redis: both supported simultaneously on same key
```

---

## Interview Quick Answers

- **Why is LRU the most common eviction policy?** — Most applications follow a "temporal locality" pattern: if you accessed something recently, you're likely to access it again soon. LRU keeps recently accessed items, which matches this pattern well. It's also O(1) to implement with a doubly-linked list + hash map.
- **When does LRU fail?** — Sequential scans: reading a large table sequentially evicts everything from the cache (each page accessed once, then never again). This "LRU pollution" can trash a previously warm cache. Fix: use CLOCK (second-chance) algorithm, or scan-resistant caches like PostgreSQL's clock-sweep.
- **What is the difference between TTL eviction and LRU eviction?** — TTL evicts entries after a fixed duration regardless of usage. LRU evicts the least recently accessed entry when capacity is exceeded. TTL handles data freshness (stale invalidation). LRU handles capacity (memory pressure). Use both together.
