# Consistent Hashing

## The Rebalancing Problem

With simple hash sharding, adding a new node remaps almost all keys:

```
3 nodes: key → node = hash(key) % 3
4 nodes: key → node = hash(key) % 4
→ Different result for 75% of keys → must move 75% of data

With 100 GB of data: 75 GB must be transferred!
During migration: service degraded, performance spikes
```

Consistent hashing solves this: adding/removing a node moves only `1/N` fraction of keys (N = number of nodes).

---

## Consistent Hashing: The Ring

```
The ring: a circular hash space from 0 to 2³² (or 2⁶⁴)

Step 1: Hash each node to a position on the ring
  hash("Node-A") → 12
  hash("Node-B") → 45
  hash("Node-C") → 78

  Ring (0 to 100 simplified):
  
     0
     │
  ───┼─────── 12 (Node A)
     │
  ───┼─────── 45 (Node B)
     │
  ───┼─────── 78 (Node C)
     │
  ─ 100 ────── (wraps back to 0)

Step 2: Hash each key to a position on the ring
  hash("user:1234") → 30
  hash("user:5678") → 60
  hash("user:9999") → 90

Step 3: Each key is owned by the first node clockwise from it
  hash("user:1234") = 30 → next clockwise node = Node B (45)
  hash("user:5678") = 60 → next clockwise node = Node C (78)
  hash("user:9999") = 90 → wraps around → Node A (12)
```

---

## Adding and Removing Nodes

```
Add Node D at position 65:

  Old:  user:5678 (pos 60) → Node C (78)
  New:  user:5678 (pos 60) → Node D (65)  ← Node D is closer!

Only keys between 45 (Node B) and 65 (new Node D) need to move:
  Before: owned by Node C (78)
  After:  owned by Node D (65)
  → Only 1/4 of Node C's keys move (roughly 1/N fraction)

Remove Node C (78):
  Keys owned by C (65 to 78) move to Node A (next clockwise = wraps to A at 12)
  → Only C's keys move, nothing else changes

Benefits:
  ✓ Adding 1 node: moves ~1/N fraction of data
  ✓ Removing 1 node: moves only that node's data
  ✓ No global reshuffling!
```

---

## Virtual Nodes (vnodes)

The naive ring has a problem: with 3 physical nodes, each handles ~33% of the ring. After adding Node D, load might be:
- Node A: 30% (still large arc)
- Node B: 20% (small arc)  
- Node C: 15% (smaller arc after D took some)
- Node D: 35% (took a big section from C)

Load is uneven! **Virtual nodes** solve this:

```
Instead of 1 ring position per physical node, assign many:

Node A → positions 5, 25, 55, 82  (4 virtual nodes)
Node B → positions 11, 38, 67, 91
Node C → positions 18, 44, 72, 97

Now the ring looks like:
  5  11  18  25  38  44  55  67  72  82  91  97
  A   B   C   A   B   C   A   B   C   A   B   C

Each node owns 4 non-contiguous arcs → more uniform load distribution

Number of vnodes per physical node:
  DynamoDB: 100s of vnodes per node
  Cassandra: configurable (vnodes = 256 default in modern Cassandra)
  Benefit: adding a new physical node takes small arcs from MANY existing nodes
           → very uniform load after rebalancing
```

---

## Consistent Hashing with Replication

For fault tolerance, each key is replicated across multiple nodes:

```
Replication factor = 3:
  Each key is stored on the 3 consecutive clockwise nodes

  hash("user:1234") = 30:
    Primary replica: Node B (45)
    Second replica:  Node C (78)
    Third replica:   Node A (12, wraps around)

Ring with vnodes and replication (Cassandra):
  ┌──────────────────────────────────────────────────────────────┐
  │  Ring:  A   B   C   A   B   C   A   B   C   ...             │
  │                                                              │
  │  Write user:1234 with RF=3:                                  │
  │    Primary: B (next clockwise)                               │
  │    Replica 1: C (next unique node)                           │
  │    Replica 2: A (next unique node)                           │
  │                                                              │
  │  Read with QUORUM (2/3):                                     │
  │    Ask B, C, A → wait for 2 responses                        │
  │    Return most recent timestamp                              │
  └──────────────────────────────────────────────────────────────┘
```

---

## Real Systems Using Consistent Hashing

```
System        Implementation                    Notes
──────────────────────────────────────────────────────────────────
Amazon        Original consistent hashing paper  "Dynamo" paper (2007)
DynamoDB      Ring + vnodes + preference list   Quorum reads/writes
Cassandra     Murmur3 hash ring + 256 vnodes    Token ranges per node
Riak          Ring with 64 partitions default   Handoff on failure
Chord P2P     Ring + finger tables              O(log N) routing
CDN load bal. Ring for origin selection         Sticky sessions
Redis Cluster Hash slots (16384 total)          Consistent but not ring-based (slots)
```

### Redis Cluster Hash Slots

```
Redis Cluster uses 16,384 hash slots (a simplified consistent hashing variant):

  hash_slot = CRC16(key) % 16384

  3 primary nodes divide the slots:
    Node A: slots 0-5460     (~1/3)
    Node B: slots 5461-10922 (~1/3)
    Node C: slots 10923-16383 (~1/3)

Adding Node D:
  Move 1/4 of slots from each existing node to D:
    Node A keeps 0-4095   (gives 4096-5460 to D)
    Node B keeps 5461-8191 (gives 8192-10922 to D)
    Node C keeps 10923-13652 (gives 13653-16383 to D)
    Node D: 4096-5460, 8192-10922, 13653-16383
```

---

## Interview Quick Answers

- **Why is consistent hashing better than modulo hashing for distributed systems?** — Modulo hashing (`hash(key) % N`) remaps ~(N-1)/N keys when N changes. Consistent hashing remaps only ~1/N keys when adding a node and only that node's keys when removing. This makes adding/removing capacity nearly zero-downtime operations.
- **What are virtual nodes and why are they used?** — Each physical server is assigned multiple positions (virtual nodes) on the ring. More positions → more uniform load distribution. When a new physical node joins, it takes small arcs from many existing nodes → very even rebalancing.
- **How does Cassandra use consistent hashing?** — Each node is assigned a range of a 64-bit token space (the ring). Each key is hashed to a token with Murmur3. The key is owned by the node whose token range includes that token. With virtual nodes (256 per physical node), load is very uniform.
