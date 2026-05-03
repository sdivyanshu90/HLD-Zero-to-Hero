# Virtual Nodes and Rebalancing

## Why Rebalancing is Hard

When you add or remove nodes from a distributed database, data must be redistributed. Doing this while serving live traffic requires:

1. No downtime (requests continue being served)
2. No data loss (every key accessible at all times)
3. Minimal performance impact (rebalancing I/O doesn't starve user requests)
4. Consistency (data not lost or duplicated during the move)

---

## Rebalancing with Virtual Nodes

```
Physical topology:
  3 physical nodes (A, B, C), each responsible for some token ranges

  With vnodes (each physical node = 3 virtual nodes):
    A → tokens: [0-10], [40-50], [70-80]
    B → tokens: [10-20], [50-60], [80-90]
    C → tokens: [20-30], [60-70], [90-100]

Adding Node D:
  Each existing node gives ~1/4 of its vnodes to D:
    A gives [40-50] to D
    B gives [80-90] to D
    C gives [20-30] to D

  New state:
    A → [0-10], [70-80]           (lost 1 vnode)
    B → [10-20], [50-60]          (lost 1 vnode)
    C → [60-70], [90-100]         (lost 1 vnode)
    D → [20-30], [40-50], [80-90] (new node, 3 vnodes)

  Data moved: ~25% from A + 25% from B + 25% from C = ~25% total data
  Traffic during rebalancing: read old owner OR new owner (handled by coordinator)
```

---

## The Handoff Protocol (Cassandra / Riak)

```
When a node is temporarily unavailable (not removed, just down):
  Hinted Handoff:
    Writes intended for down Node C are held by another node (Node A)
    as "hints" (small metadata records)
    When C comes back online: Node A delivers the hints
    C replays them and catches up

When a node is permanently removed:
  Bootstrap/Streaming:
    New node D announces its token ranges
    Current owners stream data to D:
      A streams [40-50] data to D
      B streams [80-90] data to D
      C streams [20-30] data to D
    Once complete: D takes ownership of those ranges
    D is now live in the ring
```

---

## Rebalancing Strategies

### Move-Based Rebalancing

```
Steps:
  1. Identify current token assignments
  2. Calculate target token assignments (equal distribution)
  3. For each token range being moved:
     a. New owner starts receiving writes (dual writes)
     b. Existing data streamed from old owner to new owner
     c. New owner takes over reads when caught up
     d. Old owner stops serving that range

  Atomic handoff per token range:
    Old owner → still primary
    New owner → receiving stream + writes
    Flip: New owner becomes primary
    Old owner → no longer serves range

  Cassandra MOVE/BOOTSTRAP command:
    nodetool move [newtoken]   # move to a new position on the ring
    nodetool bootstrap          # bootstrap a new node into the cluster
```

### Load-Aware Rebalancing

```
Simple vnodes assign tokens uniformly in hash space.
But data distribution ≠ uniform if keys are skewed.

Load-aware rebalancing:
  Monitor actual load per shard (CPU, disk, request rate)
  Identify overloaded shards
  Move token ranges away from overloaded shards to underloaded shards

  DynamoDB: automatic partition splitting
    When a partition exceeds 10 GB or 3,000 RCU/1,000 WCU:
    DynamoDB automatically splits it into two partitions
    No manual intervention needed

  Cassandra: manual but guided
    Run: nodetool status (see load per node)
    nodetool rebalance → calculate new token assignments for uniform load
```

---

## The Rebalancing During Compaction Problem

```
Challenge: adding a node triggers both rebalancing AND compaction simultaneously

  Adding Node D to a Cassandra cluster:
    Streaming data FROM existing nodes TO Node D  → high network I/O
    Compaction running on Node D as it receives data → high disk I/O
    Read requests still arriving → competing with both

  Solution: throttle streaming
    cassandra.yaml: stream_throughput_outbound_megabits_per_sec: 200
    Limits streaming to 200 Mbps (leaves bandwidth for user requests)
    Rebalancing takes longer but doesn't starve users

  Cassandra bootstrap duration example:
    5 TB cluster, 3 nodes, adding 1 node (move 1.67 TB to new node)
    At 200 Mbps: 1.67 TB / 200 Mbps = 1.67 TB / (25 MB/s) = 67,000 seconds!
    (~18 hours if throttled to protect user traffic)
    → Plan rebalancing carefully, not during peak traffic hours
```

---

## Resharding (Hash-Based Sharding)

When not using consistent hashing and you need to add shards:

```
Double-write migration pattern:
  Phase 1: Write to both old and new clusters
    - All new writes go to OLD cluster (primary) AND NEW cluster
    - Old cluster still serves all reads

  Phase 2: Backfill old data
    - Copy historical data from old cluster to new cluster
    - Use a comparison tool to find and fix discrepancies

  Phase 3: Verify
    - New cluster has all data
    - Run verification queries: compare counts, sample rows

  Phase 4: Switch reads
    - Route read traffic to new cluster
    - Monitor error rates, latency, data correctness

  Phase 5: Stop double-writes
    - Write only to new cluster
    - Decommission old cluster

  Total migration time for large cluster: weeks to months
  This is why you want to get sharding right the first time!
```

---

## Interview Quick Answers

- **How does adding a node to a Cassandra cluster affect existing data?** — Each existing node gives up some of its token ranges (vnodes) to the new node. The data in those ranges is streamed from existing nodes to the new one. With consistent hashing + vnodes, only ~1/N fraction of data moves (N = new cluster size). Streaming is throttled to protect live traffic.
- **What is hinted handoff in Cassandra?** — When a target replica is temporarily down, another node holds the write as a "hint." When the down node recovers, the hint is delivered and the node replays it to catch up. This avoids read-repair overhead and ensures the down node converges quickly.
- **How does DynamoDB handle hot partitions?** — Automatic partition splitting: when a partition exceeds 10 GB or its provisioned throughput limits, DynamoDB splits it into two partitions and redistributes its capacity. For extreme hot keys (celebrity users), DynamoDB also offers request routing to a larger pool of servers.
