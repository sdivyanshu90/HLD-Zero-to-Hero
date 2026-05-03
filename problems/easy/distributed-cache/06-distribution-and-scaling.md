# Step 6 — Distribution and Scaling

## Consistent Hashing — Why It Matters

**Naive modulo hashing:**
```
node = hash(key) % N

If N changes from 3 to 4:
  Nearly all keys remap to different nodes
  → massive cache stampede on node add/remove
```

**Consistent hashing:**
```
Place nodes on a ring [0, 2^32)
Each key maps clockwise to the next node

Adding node D between B and C:
  Only keys in (B, D] need to move to D
  All other keys stay put

Typical rehash fraction: 1/N of keys (vs. nearly all with modulo)
```

## Virtual Nodes

```
Without virtual nodes:
  3 real nodes → uneven distribution if hashes cluster

With 150 virtual nodes per real node:
  Node A → A_0, A_1, ..., A_149  (150 points on ring)
  Node B → B_0, B_1, ..., B_149
  Node C → C_0, C_1, ..., C_149

Distribution becomes uniform; large nodes get proportionally more vnodes
```

## Replication for High Availability

```
For each key, write to primary node + 1 replica:
  Primary: Node A (at hash position)
  Replica: Node B (next node clockwise)

On Node A failure:
  Client ring detects A is down
  Routes reads to Node B (stale by at most write lag)
  Writes route to B until A recovers
```

## Redis Cluster Mode

```
16384 hash slots distributed across nodes:
  Node 1: slots 0-5460
  Node 2: slots 5461-10922
  Node 3: slots 10923-16383

slot = CRC16(key) mod 16384

On node failure:
  Replica promotes to primary (automatic failover, ~1-2s)
  Cluster continues serving affected slots
```

## Scaling Out: Adding a Node

```
Step 1: Spin up new Redis instance
Step 2: CLUSTER MEET <new-ip> <new-port>
Step 3: CLUSTER REBALANCE (migrates ~1/N of slots)
Step 4: Old slots now served by new node
Total migration time: minutes for GBs of data
```

## Hot Key Problem

```
Problem: One key (e.g., a celebrity tweet) gets 100K req/sec
  → overloads the single responsible node

Solutions:
  1. Local in-process cache (e.g., Caffeine) in each app server
     → absorbs 99% of traffic before hitting Redis
  
  2. Key replication: store N copies with suffix
     key_0, key_1, ..., key_{N-1}
     client picks random key_{random(0,N)}
     → distributes load across N nodes
  
  3. Read replicas per Redis slot (Redis 7.x feature)
```
