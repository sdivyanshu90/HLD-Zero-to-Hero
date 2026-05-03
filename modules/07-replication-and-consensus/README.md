# Module 07: Replication and Consensus

## Overview

Replication gives you fault tolerance and read scalability. Consensus gives you the ability to coordinate across nodes without risk of split-brain. Together, they form the backbone of any highly available distributed system.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│             MODULE 07 LEARNING MAP                              │
│                                                                  │
│  01-replication-topologies                                      │
│     └── Single-leader, multi-leader, leaderless                │
│         Quorum reads/writes, read repair                       │
│                    │                                            │
│                    ▼                                            │
│  02-synchronous-vs-async-replication                           │
│     └── Sync (RPO=0), async (better throughput)                │
│         Semi-sync, Patroni failover automation                 │
│                    │                                            │
│                    ▼                                            │
│  03-quorum-math                                                 │
│     └── W+R>N equation, failure tolerance math                 │
│         Cassandra levels, hinted handoff, read repair          │
│                    │                                            │
│                    ▼                                            │
│  04-split-brain-and-fencing                                     │
│     └── Split-brain problem, fencing tokens                    │
│         STONITH, distributed locking pitfalls                  │
│                    │                                            │
│                    ▼                                            │
│  05-consensus-basics                                            │
│     └── Paxos phases, Raft (leader election, log replication)  │
│         Where consensus is used (etcd, ZK, CockroachDB)        │
└────────────────────────────────────────────────────────────────┘
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-replication-topologies.md](01-replication-topologies.md) | Single/multi-leader, leaderless, failover |
| [02-synchronous-vs-asynchronous-replication.md](02-synchronous-vs-asynchronous-replication.md) | Sync/async trade-offs, RPO/RTO |
| [03-quorum-math.md](03-quorum-math.md) | W+R>N, Cassandra consistency levels |
| [04-split-brain-and-fencing.md](04-split-brain-and-fencing.md) | Split-brain, fencing, STONITH |
| [05-consensus-basics.md](05-consensus-basics.md) | Paxos, Raft, production use |
| [06-checkpoint.md](06-checkpoint.md) | Self-test questions |
