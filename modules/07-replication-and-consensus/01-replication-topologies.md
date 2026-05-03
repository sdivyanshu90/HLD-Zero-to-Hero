# Replication Topologies

## Why Replicate?

Replication creates multiple copies of data on different nodes to achieve:

```
Goals of replication:
  1. Fault tolerance: if one node fails, others continue serving data
  2. Read scalability: spread read load across multiple replicas
  3. Geographic distribution: serve reads from the nearest datacenter
  4. Zero-downtime maintenance: take one replica offline, rotate through

Key question: when does a write "count"?
  → Determines the consistency vs availability trade-off
  → This is the core of all replication design
```

---

## Topology 1: Single-Leader (Primary-Replica)

```
                    ┌────────────────────────────────────────────┐
                    │          SINGLE-LEADER REPLICATION          │
                    │                                              │
  Writes ─────────▶ │  ┌──────────┐                              │
                    │  │ Primary  │ ← only node accepting writes  │
  Reads (strong) ──▶│  │  (R+W)   │                              │
                    │  └────┬─────┘                              │
                    │       │  replication stream                 │
                    │  ┌────┴────────────────────────┐           │
                    │  ▼                             ▼            │
                    │  ┌──────────┐         ┌──────────┐         │
  Reads ───────────▶│  │Replica 1 │         │Replica 2 │◀─ Reads │
                    │  │ (Read)   │         │ (Read)   │         │
                    │  └──────────┘         └──────────┘         │
                    └────────────────────────────────────────────┘

Examples: PostgreSQL streaming replication, MySQL binlog replication,
          MongoDB replica set (1 primary + N secondaries)
```

### Single-Leader: Failover

```
Primary fails:
  1. Replica detects primary is gone (missed N heartbeats)
  2. Election: replicas vote for new primary
     → Typically: replica with highest replication offset wins
     → Ensures new primary has most up-to-date data
  3. New primary takes over
  4. Old primary comes back: must become a replica (cannot have two primaries)

Problems:
  Asynchronous replication lag:
    Old primary committed N writes
    Replica was N-K writes behind
    New primary is missing K writes!
    → Application sees those K writes "disappear" after failover

  Split-brain:
    Network partition: both replicas think the other is dead
    Both elect themselves as primary
    → Two primaries accepting writes simultaneously
    → Data diverges, requires manual merge later

  Mitigation:
    STONITH (Shoot the Other Node In The Head): power off old primary
    before new primary starts accepting writes
    Fencing tokens: increment a monotonically increasing token; old primary
    with lower token is rejected by storage systems
```

---

## Topology 2: Multi-Leader

```
                    Datacenter A                  Datacenter B
                    ┌───────────────┐             ┌───────────────┐
  Writes (DC-A) ──▶ │   Leader A    │ ◄──────────▶│   Leader B    │ ◄── Writes (DC-B)
                    │               │  async repl  │               │
                    │               │             │               │
                    └───────┬───────┘             └───────┬───────┘
                            │                             │
                         ┌──▼──┐                       ┌──▼──┐
                         │Rep 1│                       │Rep 3│
                         └─────┘                       └─────┘

Advantages:
  ✓ Writes served locally (low latency in each DC)
  ✓ Continues working if inter-DC link fails (AP behavior)
  ✓ Geographic redundancy + local writes

Disadvantages:
  ✗ CONFLICT RESOLUTION REQUIRED when same key written in both DCs
  ✗ "Write conflict": User updates profile in DC-A and DC-B simultaneously
  
Conflict resolution strategies:
  1. Last-Write-Wins (LWW): higher timestamp wins
     Simple but loses data (lower-timestamp write silently discarded)
  
  2. Application-level merge: e-commerce "add to cart" → union of both carts
     Works for commutative/set-like operations
  
  3. Conflict flagging: mark conflicting writes, force user to resolve
     GitHub-style merge conflict on documents

Examples: MySQL Group Replication, CouchDB, Cassandra (multi-DC tunable)
Active-active geo-distributed: Google Docs, Notion, collaborative editors
```

---

## Topology 3: Leaderless Replication

```
No designated primary. Client writes to ALL nodes (or a quorum).

                    Node A   Node B   Node C
  Write: x=5 ──────▶[x=5] ──▶[x=5] ──▶[x=5]
  (writes to all 3 nodes simultaneously)
  If Node B is down:  [x=5] ──▶[   ] ──▶[x=5]   (2/3 = quorum → success!)

  Read:               [x=5] ──▶[   ] ──▶[x=5]
  (reads from all 3, returns highest version)
  Node B comes back with stale x=3 → read repair: update Node B to x=5

Examples: Amazon Dynamo, Apache Cassandra, Riak

Quorum math:
  N = total replicas (replication factor)
  W = write quorum (minimum nodes that must acknowledge write)
  R = read quorum (minimum nodes that must respond to read)
  
  Consistency condition: W + R > N
  Example: N=3, W=2, R=2: 2+2=4>3 → strong consistency
           N=3, W=1, R=1: 1+1=2<3 → eventual consistency (faster)
           N=3, W=3, R=1: 3+1=4>3 → strong consistency, slow writes
```

---

## Replication Lag

```
Async replication: primary ACKs write before replicas confirm
→ Replicas may be behind the primary by seconds to minutes

Problems caused by replication lag:
  1. "Read your own writes" violation
     User posts tweet → primary shows tweet
     User refreshes → reads from replica → tweet not visible yet!
     Fix: read from primary for a short window after a write

  2. "Monotonic reads" violation
     User reads time=100ms, sees message
     User reads time=200ms (from more-lagged replica) → message gone!
     Fix: session-based routing (always send a user to the same replica)

  3. "Consistent prefix reads" violation
     Conversation: A asks question → B answers
     If answer is replicated before question: reader sees answer without question
     Fix: related writes go to the same shard/node (causal consistency)
```

---

## Interview Quick Answers

- **What is the difference between single-leader and multi-leader replication?** — Single-leader: one node accepts all writes, replicas are read-only. Simple, no write conflicts. Multi-leader: multiple nodes accept writes, async replication between leaders. Enables local writes in multiple DCs but requires conflict resolution.
- **What is the "split-brain" problem?** — When a network partition causes two nodes to each believe the other is dead and both become primary. Two primaries accept diverging writes. Resolved with fencing tokens or STONITH (physically powering off the suspected-down node).
- **Why is leaderless replication (Cassandra) better for high availability?** — No single coordinator whose failure requires election. Any node can accept reads and writes. With N=3, W=1, R=1: system stays up even with 2 of 3 nodes failing.
