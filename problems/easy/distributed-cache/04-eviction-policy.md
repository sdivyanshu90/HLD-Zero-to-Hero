# Step 4 — Eviction Policies

## Policy Comparison

| Policy | Evicts | Best For | Weakness |
|--------|--------|----------|----------|
| LRU | Least Recently Used | General workloads | Doesn't track frequency |
| LFU | Least Frequently Used | Skewed hot keys | Stale frequency after burst |
| FIFO | Oldest inserted | Simple, fairness | Poor for temporal patterns |
| Random | Random entry | Fast, no overhead | Unpredictable |
| TTL-based | Expired entries first | Time-sensitive data | Needs expiry set |
| ARC | Adaptive LRU+LFU | Mixed workloads | Complex implementation |

## LRU — How it Works

```
Access sequence: A B C D A B A A

LRU state (capacity=3):
After A: [A]
After B: [B A]
After C: [C B A]
After D: [D C B]   ← A evicted
After A: [A D C]   ← A re-admitted, B evicted
After B: [B A D]   ← B re-admitted, C evicted
```

## LFU — Frequency Tracking

```
Each key has a frequency counter.
On access: freq[key]++
On eviction: remove key with minimum frequency (tie → LRU among equals)

Problem: A key accessed 100× yesterday but not today stays forever.
Fix: Frequency decay — halve counters every N seconds.
```

## TinyLFU (used in Caffeine/Guava)

```
W-TinyLFU splits cache into:
  Window cache (1%)  : admits all new entries
  Probation (20%)    : newly promoted from window
  Protected (79%)    : confirmed hot entries

Admission policy: new entry only evicts if its frequency estimate
  (from Count-Min Sketch) > candidate's frequency
  → prevents scan pollution
```

## Redis Eviction Policies (maxmemory-policy)

```
noeviction       : error on write when full
allkeys-lru      : evict any key using LRU approximation
volatile-lru     : evict only keys with TTL set, using LRU
allkeys-lfu      : evict any key using LFU
volatile-lfu     : evict only TTL keys using LFU
allkeys-random   : evict any key randomly
volatile-random  : evict random TTL key
volatile-ttl     : evict TTL key with shortest remaining TTL
```

**Recommended for general use:** `allkeys-lru`  
**Recommended for session caches:** `volatile-lru`

## Redis LRU Approximation

Redis uses approximate LRU (not exact):
```
maxmemory-samples = 5  (check 5 random keys, evict LRU among them)
Higher sample count → closer to true LRU → more CPU
Default 5 is a good balance
```
