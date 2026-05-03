# Module 07 Checkpoint: Replication and Consensus

## Questions

---

**Q1.** A PostgreSQL primary has 2 async replicas. The primary crashes. What data loss is possible and how do you prevent it?

> **Answer:** With async replication, uncommitted writes in the primary's WAL buffer that haven't been shipped to replicas are LOST (typically seconds' worth of writes). Prevention: use **semi-synchronous replication** (`synchronous_commit = remote_apply` in PostgreSQL, or at minimum `remote_write`). With `remote_apply`, the primary waits until at least one replica has replayed the WAL change before ACKing the client. RPO = 0 for those committed transactions. The trade-off is slightly higher write latency (1 replication RTT).

---

**Q2.** Design a distributed lock service for a payment processing system. What consistency guarantees does it need?

> **Answer:** Needs **linearizable consistency**: a lock must be held by exactly one client at a time with no split-brain. Use:
> - **etcd** or **ZooKeeper** as the lock backend (CP systems using Raft/ZAB)
> - Lock acquisition: `SET lock_key client_id NX EX 10` (etcd) or ephemeral ZNode (ZooKeeper)
> - **Fencing token**: include the lock's revision/epoch in every storage write. Storage layer rejects writes with stale tokens.
> - **Client-side TTL**: if lock-holder process crashes, lock expires and can be re-acquired
> - NOT Redis Redlock: susceptible to clock skew and GC pause issues

---

**Q3.** In a Cassandra 5-node cluster with RF=3, you write with QUORUM and read with QUORUM. One node fails. Are reads and writes still consistent?

> **Answer:** Yes. RF=3, QUORUM=ceil(3/2)+1=2. With 5 nodes and RF=3, each key has 3 home nodes. If 1 of those 3 fails, the remaining 2 home nodes provide quorum (W=2, R=2, W+R=4>3). The system remains fully operational. If 2 of the 3 home nodes for a key fail, that specific key becomes unavailable (cannot reach quorum). The other keys (whose 3 home nodes are still up) remain available.

---

**Q4.** What is the difference between Raft term and Paxos ballot number?

> **Answer:** Conceptually equivalent: both are monotonically increasing numbers that identify a leadership epoch. A node only accepts messages from leaders with a term/ballot >= its current seen value. When a new leader is elected (Raft) or a proposer wins Phase 1 (Paxos), the term/ballot is incremented. This prevents stale leaders from committing conflicting values.

---

**Q5.** You have a 3-node etcd cluster (used by Kubernetes). How many nodes can fail before etcd loses quorum?

> **Answer:** `floor(3/2) = 1`. etcd uses Raft with majority quorum (2/3). If 2 nodes fail, only 1 remains — insufficient for quorum → etcd stops accepting writes (CP behavior). Kubernetes cannot schedule new pods, update deployments, etc. But existing pods continue running (kubelet doesn't require etcd for pod operation). To tolerate 2 failures: use 5-node etcd cluster (floor(5/2)=2).

---

## Checklist

- [ ] Single-leader: primary + async replicas, failover via election, replication lag
- [ ] Multi-leader: local writes, conflict resolution (LWW, merge, flag)
- [ ] Leaderless: quorum reads and writes, read repair, Merkle trees
- [ ] Sync vs async replication: RPO=0 (sync) vs better throughput (async)
- [ ] Semi-synchronous: best of both (1 sync replica, rest async)
- [ ] W+R>N: strong consistency condition
- [ ] Cassandra consistency levels: ONE, QUORUM, ALL, LOCAL_QUORUM
- [ ] Split-brain: two primaries, divergent writes
- [ ] Fencing tokens: prevent split-brain at storage level
- [ ] STONITH: power off suspected-failed node before promoting new primary
- [ ] Raft: leader election, log replication, committed = majority ACK
- [ ] Consensus used in: etcd (Kubernetes), ZooKeeper, CockroachDB, Consul
