# Split-Brain and Fencing

## The Split-Brain Problem

Network partitions can create a dangerous situation where two nodes both believe they are the current primary:

```
Normal state:
  Primary ◄──────────── heartbeat ──────────────▶ Replica

Network partition:
  Primary │░░░░░░░░░░░░ PARTITION ░░░░░░░░░░░░│ Replica
  (still  │                                   │ (thinks Primary is dead)
   alive!)│                                   │
          │                                   │ (promotes to new Primary!)

Result:
  Old Primary: accepts writes for keys {a, b, c...}
  New Primary: accepts writes for different clients {d, e, f...}
  
  When partition heals:
  Old Primary: x = 5 (wrote x after partition)
  New Primary: x = 7 (also wrote x after partition)
  
  → CONFLICT. Which write wins? Data is divergent.
  → If writes are financial transactions: CATASTROPHIC
```

---

## Fencing Tokens

The correct solution: give each primary a **monotonically increasing** epoch/fencing token. Storage systems reject writes from holders of lower tokens.

```
Epoch-based fencing:
  1. Node A is primary, epoch = 1
  2. Network partition occurs
  3. Node B is elected new primary, epoch = 2
  4. Network partition heals
  5. Node A (old primary, epoch=1) tries to write

  Storage system check:
    "I already accepted writes from epoch 2. Rejecting epoch=1 write."
  
  Node A's write is rejected → no split-brain!
  Node A must step down and rejoin as a replica

Implementation:
  ZooKeeper: epoch stored in ZK; any ZK-aware storage checks epoch
  etcd: leader term (revision) in lease; storage checks term
  PostgreSQL Patroni: uses etcd leader key; old primary cannot acquire
  
  Key requirement: the fencing check must happen ATOMICALLY with the write
  at the storage level — not just at the application level
```

---

## STONITH: Shoot The Other Node In The Head

Fencing at the infrastructure level: physically power off the suspected-bad node before allowing the new primary to serve writes:

```
STONITH workflow:
  1. Primary A appears to fail (heartbeat timeout)
  2. Before promoting Replica B as new primary:
  3. STONITH agent sends power-off command to Node A's IPMI/iDRAC/BMC
  4. Node A is powered off (regardless of its actual state)
  5. Now it's safe to promote B: A CANNOT write anymore

STONITH mechanisms:
  - IPMI/iDRAC: hardware management interface power control
  - EC2: terminate instance via AWS API
  - vSphere: power off VM
  - Kubernetes: delete Pod (container process killed immediately)

Trade-off:
  ✓ Guarantees no split-brain
  ✗ May power off a node that's actually healthy (false positive)
  ✗ Adds seconds to failover time

Alternative: disk fencing (SCSI reservations on shared storage)
  Only the current primary holds the SCSI reservation
  Other nodes attempting to write get I/O error → automatic fencing
```

---

## Distributed Locking and the Redlock Problem

Distributed locks are often used to ensure only one process does a critical operation. Getting this right is harder than it looks.

```
Naive distributed lock (wrong approach):
  1. Client A acquires lock from Redis: SET lock EX 10 NX
  2. Client A does critical work...
  3. Client A's process pauses (GC pause, OS scheduling, etc.) for 12 seconds
  4. Lock expires after 10 seconds
  5. Client B acquires the same lock
  6. Client A resumes (thinks it still holds the lock)
  → TWO clients hold the "lock" simultaneously!

Fix: fencing tokens in the lock:
  1. Client A acquires lock, gets token=1 from lock service
  2. Client A does work, writes to storage with token=1
  3. Client A pauses, lock expires
  4. Client B acquires lock, gets token=2
  5. Client B writes to storage with token=2
  6. Client A resumes, tries to write with token=1
  7. Storage rejects: "I already accepted token=2, won't accept token=1"

Martin Kleppmann's critique of Redlock (2016):
  Redlock uses 5 Redis nodes and requires majority (3) to acquire lock
  Problem: clock skew can cause locks to expire on some nodes early
  → Two clients can both believe they hold the lock (race condition)
  
  Redlock is NOT safe for correctness-critical distributed locking
  Use: ZooKeeper (cp ephemeral nodes), etcd (leases), or Postgres advisory locks
```

---

## Handling the "Network is Unreliable" Reality

```
Timeouts are unreliable indicators of node failure:

Possible reasons for a missed heartbeat:
  1. Node is dead → should elect new primary
  2. Node is alive but very slow (GC pause, high load)
  3. Network packet lost → node is fine, just temporary blip
  4. Network partition → node alive, just unreachable from some nodes

How long to wait before declaring node dead?

Too short (e.g., 1 second):
  → False positives: frequent unnecessary failovers
  → Flapping: elect new primary every GC pause
  
Too long (e.g., 30 seconds):
  → 30 seconds of unavailability before recovery begins
  → Acceptable for low-traffic systems
  
Practical timeouts:
  Cassandra gossip: gossip_interval=1s, phi_convict_threshold=8 (adaptive)
  PostgreSQL Patroni: ttl=30s (primary loses leadership if cannot renew for 30s)
  Kubernetes pod: livenessProbe: initialDelaySeconds=30, periodSeconds=10
  
Phi Accrual Failure Detector (Cassandra, Akka):
  Adaptive: learns the normal distribution of heartbeat intervals
  As heartbeat silence grows longer: phi score increases
  At phi=8: declare node failed
  Better than fixed timeouts in variable-latency networks
```

---

## Interview Quick Answers

- **What is split-brain and how do you prevent it?** — Split-brain: two nodes believe they are both primary and accept conflicting writes. Prevention: fencing tokens (storage rejects writes from stale-epoch primaries), STONITH (physically power off suspected-failed node), or consensus-based leader election (only one node can hold the lease).
- **Why are distributed locks harder than they seem?** — A lock with a TTL can expire while the holder is paused (GC, OS scheduling). The holder resumes thinking it holds the lock, but another client has already acquired it. Solution: fencing tokens — storage rejects writes from holders with lower token numbers.
- **What is the Phi Accrual Failure Detector?** — An adaptive failure detector that models the normal distribution of heartbeat intervals. As the silence since the last heartbeat grows relative to the expected distribution, the suspicion score (phi) increases. This adapts to network jitter better than fixed timeouts.
