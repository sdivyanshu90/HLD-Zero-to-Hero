# Cheat Sheet: Search Autocomplete

## Scale (BoE)
```
Users: 500M DAU
Search queries per user per day: 10
Total searches: 5B/day → 58K QPS read
Characters per keystroke: 1 (each keypress triggers autocomplete)
Autocomplete QPS: 58K × avg_query_length(5) = 290K autocomplete requests/second
Latency requirement: < 100ms (feels instant)
```

## Trie Data Structure

```
Vocabulary in Trie:
  "search" → [s → e → a → r → c → h] (leaf)
  "system" → [s → y → s → t → e → m] (leaf)
  "syste"  → internal node
  
  Each node stores: top-K suggestions for this prefix
  "sys" node → ["system", "systematic", "syntax"] (pre-computed top-3)
  
  Query "sys" → O(3) lookup (just walk 3 chars, read top-K list from node)
  vs. O(n) linear scan of all search terms
  
  Node storage:
    {
      prefix: "sys",
      children: {t: ..., n: ...},
      top_k: ["system", "systematic", "syntax"],  ← pre-computed and sorted!
      frequency: {system: 10M, systematic: 5M, syntax: 3M}
    }
```

## System Architecture

```
Query path (< 100ms requirement):
  User types "sys" ──▶ CDN/Cache (common prefixes cached) ──▶ Autocomplete Server
                                                                       │
                                                                  Trie lookup
                                                                  (in-memory Redis
                                                                   or local cache)
                                                                       │
                                                               return top-5 suggestions
  
  Cache layer:
    Top 10K prefixes cover 90% of all searches (power law distribution)
    Cache these in CDN or Redis with long TTL
    
Build pipeline (daily/hourly):
  Kafka: stream all search queries ──▶ Spark/Flink count frequencies
  Build new Trie from frequency counts
  Deploy new Trie atomically (blue-green: point servers to new trie)
```

## Key Design Decisions

**1. Trie storage:**
- In-memory per Trie server (fast lookup, limited by RAM)
- Sharded by prefix (A-F on server 1, G-M on server 2, etc.)
- Serialize to Redis/disk for persistence + fast startup

**2. Personalization:**
- Global trie: most popular suggestions globally
- Personal trie: user's own search history (stored in DB, blended at query time)
- Blend: 70% global + 30% personal

**3. Trie updates:**
- Don't update trie in real-time (expensive re-computation)
- Batch update: rebuild from search log every hour
- Delta updates: only update frequency counts for changed prefixes

## Unique Trick
Top-K suggestions at each node: pre-compute and store the top-5 suggestions at EVERY node in the trie. This means autocomplete is just a trie walk (O(L) where L = query length) + read the top-K list. No dynamic computation needed at query time.
