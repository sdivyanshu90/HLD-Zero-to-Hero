# ACID vs BASE

## Two Philosophies for Handling Failures

ACID and BASE are not protocols — they are philosophies about what properties a database should guarantee under failures.

```
ACID: Atomicity, Consistency, Isolation, Durability
  → "Be safe. If in doubt, don't. Sacrifice speed for correctness."
  → Traditional RDBMS (PostgreSQL, MySQL, Oracle)

BASE: Basically Available, Soft State, Eventually Consistent
  → "Be fast. Accept some uncertainty. Resolve conflicts later."
  → Most NoSQL databases (Cassandra, DynamoDB, CouchDB)
```

---

## ACID Deep Dive

### Atomicity

All operations in a transaction succeed, or none do:

```
Bank transfer: Alice pays Bob $100

Operations:
  UPDATE accounts SET balance = balance - 100 WHERE user = 'Alice';
  UPDATE accounts SET balance = balance + 100 WHERE user = 'Bob';

Without atomicity (crash between the two):
  Alice:  -$100  (money gone!)
  Bob:    +$0    (money never arrived!)
  → $100 disappeared from the system

With atomicity:
  Both succeed → committed
  If crash between them → rollback BOTH to pre-transfer state
  → No money lost, consistent state guaranteed
```

### Consistency

A transaction brings the database from one valid state to another valid state, respecting all constraints:

```
Constraints maintained:
  Balance cannot go negative (CHECK balance >= 0)
  Foreign key: order.user_id must exist in users table
  Unique: email must be unique

Transaction that would violate constraint → rolled back
→ Database always in a valid, consistent state after any transaction
```

### Isolation

Concurrent transactions do not see each other's intermediate states:

```
Isolation levels (from weak to strong):
  Read Uncommitted  → can read uncommitted data from other txns
  Read Committed    → only reads committed data (most DBs default)
  Repeatable Read   → same row read twice in same txn returns same value
  Serializable      → behaves as if transactions ran one at a time

Concurrency anomalies prevented at each level:
                     Dirty Read  Non-Repeatable  Phantom Read
Read Uncommitted        ✗             ✗               ✗
Read Committed          ✓             ✗               ✗
Repeatable Read         ✓             ✓               ✗
Serializable            ✓             ✓               ✓

(✓ = prevented, ✗ = possible)
```

### Durability

Once a transaction is committed, it survives crashes:

```
How durability works:
  1. Transaction log (WAL) written to disk (fsync)
  2. Only then: "commit" returned to client
  3. On crash: replay WAL to recover committed state

Without durability:
  Client receives "Success"
  Server crashes 1ms later
  Data in RAM is lost
  → Client thinks the transaction happened, DB has no record of it
  → Data corruption!
```

---

## BASE Deep Dive

### Basically Available

The system is always accessible, even if individual nodes fail:

```
Cassandra 3-node cluster, one node fails:
  Without BASE: system goes down (cannot serve without full quorum)
  With BASE: remaining 2 nodes serve reads/writes at QUORUM
  → System continues (with degraded durability until node recovers)
```

### Soft State

The state of the system may change over time, even without new input, as replicas converge:

```
Replica A: like_count = 1,048 (just got 3 new likes)
Replica B: like_count = 1,045 (hasn't received the new likes yet)

State is "soft" — Replica B's state will update as replication catches up
The system does not have a single fixed "current state" at any moment
```

### Eventually Consistent

Given no new writes, all replicas will converge to the same value:

```
Timeline:
  t=0:  Write like_count = 1,048 to Node A
  t=0:  Nodes B and C still show 1,045
  t=10ms: Replication reaches Node B → 1,048
  t=20ms: Replication reaches Node C → 1,048
  t=20ms+: All nodes converge to 1,048

"Eventually" means milliseconds to seconds in practice (not hours/days)
Unless there's a network partition, then potentially longer
```

---

## Conflict Resolution in BASE Systems

When two writes conflict (concurrent writes to the same key on different nodes):

### Last Write Wins (LWW)

```
Node A receives: set x = 5  at time 1000ms
Node B receives: set x = 7  at time 1002ms

LWW: x = 7 (higher timestamp wins)

Problem: clocks are not perfectly synchronized across nodes
  Node A's clock may be 10ms ahead of Node B's
  "Earlier" write may actually have higher timestamp → data loss
```

### Version Vectors (Vector Clocks)

```
Riak/DynamoDB use vector clocks to track causality:

Node A processes write: x = 5, VC = {A:1}
Node B processes write: x = 7, VC = {A:1, B:1}

If Node C has x = 5, VC = {A:1}:
  Compare with {A:1, B:1}: B:1 > B:0 → B's version is descendant
  → Use Node B's value (no conflict, B simply has a later write)

If Node C has x = 9, VC = {C:1} (concurrent with A and B):
  {C:1} and {A:1, B:1} are concurrent → CONFLICT
  → Return both to application to resolve (Amazon: show both versions)
  → Application merges: "add to cart" is union of both carts
```

### CRDTs (Conflict-Free Replicated Data Types)

```
Mathematical data structures designed for AP systems:
  Operations are commutative, associative, idempotent
  Any order of merge produces the same result → no conflicts

G-Counter (grow-only counter):
  Each node has its own counter slot: [A:5, B:3, C:2]
  Total = sum of all = 10
  Merge: take max of each slot: [A:5, B:4, C:2] merged with [A:4, B:4, C:3]
       = [A:5, B:4, C:3] → total = 12

G-Set (grow-only set):
  Add items, never remove
  Merge: union of both sets → always converges

OR-Set (observed-remove set):
  Supports add and remove with causality tracking
  Used by: collaborative editing (adds/removes in text)

Used by: Riak CRDT types, Redis CRDT (Redis Enterprise), Akka distributed data
```

---

## ACID vs BASE: Choosing

| Requirement | ACID | BASE |
|-------------|------|------|
| Financial transactions | ✓ Required | ✗ |
| Social media likes | ✗ Overkill | ✓ |
| Inventory management | ✓ (oversell risk) | Risky |
| Session data / caches | Overkill | ✓ |
| Audit logs (append-only) | ✓ | ✓ (with care) |
| Global high write throughput | Difficult | ✓ |
| Multi-step workflows | ✓ (SAGA alternative) | ✓ (SAGA pattern) |

---

## Interview Quick Answers

- **What is "eventually consistent"?** — All replicas will converge to the same value given no new writes. In practice, milliseconds to seconds. The system accepts reads from any replica including stale ones.
- **When is eventual consistency dangerous?** — Reading your own writes from a different replica (show "liked" then reload shows "not liked"). Inventory overselling (two replicas both show 1 remaining item → both sell it). Fix: route reads to primary, or use conditional writes.
- **What is a CRDT?** — Conflict-Free Replicated Data Type. A data structure where any merge order produces the same result. Counters, sets, maps can be CRDTs. Eliminates manual conflict resolution in AP systems.
