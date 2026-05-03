# Step 4 — Trie and Prefix Index

## Trie Structure

```
Trie node stores top-K suggestions at each prefix:

     (root)
     /    \
   'a'    'b'
   / \     |
 'p' 'n'  'b'
  |        |
 'p'      'b'
  |        |
 'l'      'l'
  |        |
 'e'      'e'

Each node stores: top_k = [(score, term), ...]
"app" node: top_k = [
    (10M, "apple"),
    (8M,  "apple watch"),
    (6M,  "app store"),
    (5M,  "apple id"),
    (4M,  "applications")
]
```

## Pre-Computed Top-K at Each Node

```
Why: Computing top-K from leaf children is O(N) per query
Fix: Pre-compute and store top-K at EVERY node

Build time:
  1. Count frequency for every complete search term
  2. Bottom-up: each node stores union of children's top-K
  3. Stored in Redis: HSET trie:app top_k '[["10M","apple"],...]'

Query time:
  1. Look up HGET trie:{prefix} top_k  → O(1) Redis lookup
  2. Return pre-computed list
```

## Redis Storage of Trie

```python
# Store prefix → top-K suggestions
def store_suggestions(prefix: str, suggestions: list):
    key = f"ac:{prefix}"
    redis.setex(key, 86400, json.dumps(suggestions))

# Query
def get_suggestions(prefix: str) -> list:
    key = f"ac:{prefix}"
    data = redis.get(key)
    return json.loads(data) if data else []

# Memory estimate:
# 26^6 ≈ 300M distinct 6-char prefixes (too many)
# In practice: only store prefixes with ≥ 100 searches
# ~10M meaningful prefixes × 500B = 5 GB → fits in Redis cluster
```

## Prefix Sharding

```
Shard trie by first character:
  Shard 0: prefixes a*
  Shard 1: prefixes b*
  ...
  Shard 25: prefixes z*

Or by first 2 characters:
  26^2 = 676 shard buckets → map to N Redis nodes

Client routes by: hash(prefix[:2]) % N
```

## Trie Rebuild (Batch, Daily)

```
1. Spark job reads search logs from S3 (past 7 days)
2. Counts: (search_term → frequency)
3. Normalizes: lowercase, strip punctuation, deduplicate
4. Builds trie in memory, computes top-K at each node
5. Serializes to Redis (pipeline: ~10M SETEX commands)
6. Swaps active prefix: writes to "ac_v2:*", then atomically
   rename "ac_v2" → "ac" (blue-green deployment of trie)
7. Old trie keys expire naturally (TTL 48h)

Rebuild time: ~20 min for 10M prefixes on 8-node Spark cluster
```

## Incremental Updates (Real-Time)

```
For "trending now" suggestions (viral events):
  Kafka stream of search queries
  Count-Min Sketch: approximate frequency per query
  Every 10 min: update top-K for affected prefixes in Redis
  Lag: ~10 min for new trending term to appear in suggestions
```
