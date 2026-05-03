# CAP Theorem

## The Theorem

In the presence of a **network partition**, a distributed system can guarantee at most two of:

- **Consistency (C)**: Every read receives the most recent write or an error
- **Availability (A)**: Every request receives a (non-error) response, possibly stale
- **Partition Tolerance (P)**: The system continues operating despite network partitions

```
┌────────────────────────────────────────────────────────────────┐
│                        CAP TRIANGLE                             │
│                                                                  │
│                      Consistency                                │
│                          ▲                                      │
│                         /│\                                     │
│                        / │ \                                    │
│                       /  │  \                                   │
│             CP       /   │   \  CA                             │
│          (MongoDB, /     │     \ (single-node DB)              │
│           HBase)  /      │      \                              │
│                  /  NOT  │ REAL  \                              │
│                 /  SAFE  │SYSTEM \                              │
│                ▼─────────┼────────▼                             │
│   Partition ──────────────────────── Availability              │
│   Tolerance            AP             Tolerance                │
│                  (Cassandra, DynamoDB,                         │
│                   CouchDB, Riak)                               │
│                                                                  │
│  CA is only possible without partitions → not a real choice     │
│  for distributed systems                                         │
└────────────────────────────────────────────────────────────────┘
```

---

## Why P is Not Optional

Network partitions are inevitable in distributed systems. Packets get lost, switches fail, datacenter links go down. You cannot design around the possibility of partitions — you can only choose how to respond.

```
Partition scenario:
  ┌─────────────────────────────────────────────────┐
  │                                                  │
  │  Node A ────────────✗──────────── Node B        │
  │  (has writes)    PARTITION        (stale data)  │
  │                                                  │
  │  Client reads from Node B:                       │
  │                                                  │
  │  CP choice: Node B returns ERROR                 │
  │  "Cannot guarantee consistency, refusing read"   │
  │                                                  │
  │  AP choice: Node B returns STALE DATA           │
  │  "Here's the data I have, may be outdated"      │
  │                                                  │
  └─────────────────────────────────────────────────┘
```

---

## CP Systems: Consistency over Availability

When partitioned, CP systems reject requests to maintain consistency:

```
CP Databases: HBase, Zookeeper, etcd, Consul, MongoDB (majority reads)

Example: Bank transfer during partition:
  Primary is partitioned from replica
  CP: replica refuses to serve reads/writes (returns error)
  → Clients see errors, but no stale balance shown

Behavior:
  Normal operation: reads and writes succeed
  Network partition: minority nodes refuse requests (no quorum)
  → System is unavailable during partition
  → But no stale/inconsistent data is ever returned
```

**Use CP when**: correctness is more important than availability. Financial systems, configuration management (etcd), distributed locks.

---

## AP Systems: Availability over Consistency

When partitioned, AP systems serve potentially stale data:

```
AP Databases: Cassandra, DynamoDB, CouchDB, Riak, DNS

Example: Social media like counter during partition:
  Datacenter A: like_count = 1,050
  Datacenter B (partitioned): like_count = 1,040
  AP: both serve their local value (different values!)
  → After partition heals: conflict resolved (take max → 1,050)

Behavior:
  Normal operation: fast reads and writes
  Network partition: all nodes continue serving (possibly stale)
  After partition heals: conflict resolution kicks in
  → Eventual consistency
```

**Use AP when**: availability is more important than strict consistency. Social media, shopping carts, DNS, content delivery, metrics/analytics.

---

## Common Misunderstandings

### Misunderstanding 1: CA is a valid choice

```
CA systems "sacrifice" partition tolerance.
In a single-node database (SQLite, single Postgres): there's no partition possible.
→ "CA" means you don't have a distributed system, not that you chose CA.

Any distributed system must handle partitions.
Real choice for distributed systems: CP or AP.
```

### Misunderstanding 2: CAP is binary

CAP is actually on a spectrum. Modern distributed databases often tune consistency per-operation:

```
Cassandra consistency levels (you choose per query):

  ONE     → Write to 1 replica, return success. Fast. AP.
  QUORUM  → Write to majority of replicas. Balanced. CP-leaning.
  ALL     → Write to every replica. Slow. CP.
  LOCAL_QUORUM → Write to majority in local datacenter. Geo-aware.

  Read:  QUORUM + Write: QUORUM → strong consistency (W+R > N)
  Read:  ONE    + Write: ONE    → eventual consistency (fastest)
```

### Misunderstanding 3: CAP is the only theorem

PACELC adds latency as a dimension even when no partition exists.

---

## CAP in Real Systems

```
System        | CAP Choice | Reason
──────────────────────────────────────────────────────────
Zookeeper     | CP         | Leader election, config: must be accurate
etcd          | CP         | Kubernetes state: wrong config = broken cluster
HBase         | CP         | Built on HDFS, uses ZooKeeper for coordination
MongoDB       | CP (default)| Primary-only writes, majority reads
Cassandra     | AP         | Always-on availability more important than perfect consistency
DynamoDB      | AP (default)| Eventual consistency by default (can request strong)
CouchDB       | AP         | Multi-master replication, conflict resolution
Riak          | AP         | Designed for availability under network faults
Redis         | CP-ish     | Single leader, but sentinel failover has window of inconsistency
DNS           | AP         | TTL-based eventual consistency intentional by design
```

---

## Real-World CAP Scenario: Shopping Cart

Amazon famously wrote about choosing AP for shopping carts:

```
Scenario: User adds item to cart. Network partition occurs.
  Datacenter A has the cart with item X
  Datacenter B has old cart without item X

CP choice:
  User cannot add items during partition → orders of magnitude of lost sales

AP choice:
  User can still add items during partition
  Both datacenters have their version
  On partition heal: merge both carts (take union of items)
  → User might see a few extra items in cart → minor confusion
  → Much better than "service unavailable"

Amazon chose AP + conflict resolution (merge).
Financial charge? Use a different, CP path.
```

---

## Interview Quick Answers

- **What is CAP theorem?** — A distributed system can guarantee at most 2 of: Consistency (fresh reads), Availability (every request gets a response), Partition Tolerance (works despite network failures). Since partitions are inevitable, the real choice is CP vs AP.
- **Why is CA not a real option?** — CA means no partition tolerance, which means you can't have a distributed system. Single-node databases are effectively CA, but that's not a distributed system.
- **When would you choose CP over AP?** — When stale reads are worse than unavailability: financial systems, inventory (overselling is worse than being down), distributed locking, configuration management.
- **When would you choose AP over CP?** — When availability is more important: social feeds, shopping carts, analytics, DNS, content delivery.
