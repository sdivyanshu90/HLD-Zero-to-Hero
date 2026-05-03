# Step 3 — Core Data Structures

## LRU Cache Implementation

An O(1) LRU requires:
1. **HashMap** (key → node pointer) for O(1) lookup
2. **Doubly-Linked List** to maintain recency order

```
HEAD ↔ [most-recent] ↔ ... ↔ [least-recent] ↔ TAIL

On GET(key):
  node = hashmap[key]
  move node to HEAD
  return node.value

On SET(key, value):
  if key in hashmap:
    update node.value, move to HEAD
  else:
    create new node at HEAD
    hashmap[key] = node
    if len > capacity:
      evict = TAIL.prev
      remove evict from list and hashmap
```

### Diagram

```
capacity = 3, state: A → B → C (A most recent)

GET(B):
  B → A → C   (B moved to front)
  HashMap: {B: node_B, A: node_A, C: node_C}

SET(D):   (D is new, capacity exceeded)
  D → B → A   (C evicted from tail)
  HashMap: {D: node_D, B: node_B, A: node_A}
```

## Hash Ring Data Structure

```python
import hashlib, bisect

class ConsistentHashRing:
    def __init__(self, nodes, virtual_nodes=150):
        self.ring = {}    # hash → node
        self.sorted_keys = []
        for node in nodes:
            for i in range(virtual_nodes):
                key = self._hash(f"{node.id}:{i}")
                self.ring[key] = node
                bisect.insort(self.sorted_keys, key)

    def _hash(self, s: str) -> int:
        return int(hashlib.md5(s.encode()).hexdigest(), 16)

    def get_node(self, key: str):
        h = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, h) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]
```

## Memory Layout

```
Per-entry overhead in Redis:
  Key:        variable (avg 30 B)
  Value:      variable (avg 200 B)
  Metadata:   ~64 B (LRU clock, refcount, encoding type)
  Dict entry: ~32 B (pointer + next-pointer)
  Total:     ~326 B per entry

For 1 GB cache:
  1 GB / 326 B ≈ 3.2 M entries
```

## TTL Storage

```
Option A: Separate expiry dict
  key → (value, expire_timestamp_ms)
  Lazy expiry: check on every GET
  Active expiry: background thread samples 20 random keys/100ms

Option B: Entry-embedded TTL
  Each node in the doubly-linked list stores expire_at
  Sweep LRU tail for expired entries
```
