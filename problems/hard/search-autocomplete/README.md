# Search Autocomplete — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** trie, prefix-index, CDN, top-K, personalization  
**Companies:** Google, Amazon, Twitter, LinkedIn

---

## Problem Statement

Design a search autocomplete system (like Google's search bar) that:
- Returns top 5 suggestions for any prefix in < 50 ms
- Processes 5 M searches/day to update suggestion rankings
- Handles 10 K queries per second at peak
- Supports personalization (recent searches)

---

## Architecture Diagram

```
User types "appl" in search bar
         │
         ▼
┌─────────────────────────────┐
│  CDN (top 10K prefixes)     │  cache-hit for popular prefixes
└─────────────┬───────────────┘
              │ miss
              ▼
┌─────────────────────────────┐
│  Autocomplete API Service   │
│  (stateless)                │
└─────────────┬───────────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌─────────┐      ┌──────────────┐
│  Trie   │      │  Personal    │
│ Servers │      │  History DB  │
│ (Redis) │      │  (Cassandra) │
└─────────┘      └──────────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Query Traffic and Latency](02-query-traffic-and-latency.md)
3. [Ingestion and Normalization](03-ingestion-and-normalization.md)
4. [Trie and Prefix Index](04-trie-and-prefix-index.md)
5. [Ranking and Personalization](05-ranking-and-personalization.md)
6. [Caching and Hot Prefixes](06-caching-and-hot-prefixes.md)
7. [Updates and Multi-Region Serving](07-updates-and-multi-region-serving.md)
8. [Checkpoint](08-checkpoint.md)
