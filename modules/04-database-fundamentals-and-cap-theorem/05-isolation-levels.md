# Transaction Isolation Levels

## Why Isolation Matters

When multiple transactions run concurrently, they can interfere in subtle ways. Isolation levels define what anomalies are allowed to occur:

```
Anomaly types:
  Dirty Read:         Reading uncommitted data from another transaction
  Non-Repeatable Read: Same row read twice in one txn returns different values
  Phantom Read:       A query run twice returns different sets of rows
  Lost Update:        Two transactions read-then-write the same value; one's update is lost
  Write Skew:         Two transactions read overlapping data, write non-overlapping, creating inconsistency
```

---

## The Four Standard Isolation Levels

```
┌──────────────────────────────────────────────────────────────────┐
│              ISOLATION LEVELS AND ANOMALIES PREVENTED            │
│                                                                    │
│  Level              Dirty  Non-Rep  Phantom  Lost   Write        │
│                     Read   Read     Read     Update Skew         │
│  ─────────────────────────────────────────────────────────────   │
│  Read Uncommitted   ✗      ✗        ✗        ✗      ✗           │
│  Read Committed     ✓      ✗        ✗        ✗      ✗           │
│  Repeatable Read    ✓      ✓        ✗        ✓      ✗           │
│  Serializable       ✓      ✓        ✓        ✓      ✓           │
│                                                                    │
│  ✓ = prevented  ✗ = possible                                     │
│  Stronger = more anomalies prevented = more overhead             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Each Level Illustrated

### Read Uncommitted (Almost Never Used)

```
Transaction 1:                  Transaction 2 (dirty reader):
  BEGIN;
  UPDATE balance = 500          
  WHERE user = 'Alice';         
  (not yet committed!)          
                                  SELECT balance WHERE user = 'Alice';
                                  → Returns 500 (dirty read!)
  ROLLBACK;                     
  (balance stays 400)           
                                  → Client used $500 value that never existed!
```

### Read Committed (PostgreSQL Default)

```
Transaction 1:                  Transaction 2:
  BEGIN;
  SELECT stock FROM product     
  WHERE id = 123;               
  → stock = 5                   
                                  BEGIN;
                                  UPDATE product SET stock = 3 WHERE id = 123;
                                  COMMIT;  ← committed!
  SELECT stock FROM product     
  WHERE id = 123;               
  → stock = 3  ← CHANGED!       

  This is non-repeatable read: same row read twice, different result
  Happens at Read Committed (allowed anomaly)
```

### Repeatable Read (MySQL InnoDB Default)

```
Transaction 1:                  Transaction 2:
  BEGIN;
  SELECT stock FROM product     
  WHERE id = 123;               
  → stock = 5                   
                                  UPDATE product SET stock = 3 WHERE id = 123;
                                  COMMIT;
  SELECT stock FROM product     
  WHERE id = 123;               
  → stock = 5  ← SAME! (snapshot)

Repeatable Read uses MVCC (Multi-Version Concurrency Control):
  Transaction sees a snapshot of the database as of its start time
  Updates by other committed transactions are invisible within this transaction
```

### MVCC Internals

```
PostgreSQL stores multiple versions of each row:

Row in heap:
  xmin=100  xmax=null  balance=400  ← written by transaction 100, not deleted
  xmin=101  xmax=null  balance=500  ← written by transaction 101

When Transaction 102 reads:
  Sees all rows with xmin <= 102 and (xmax is null OR xmax > 102)
  → Sees the version committed before this transaction started

Benefits:
  Readers don't block writers
  Writers don't block readers
  → High concurrency for mixed read/write workloads

Cost:
  Multiple row versions take space → need VACUUM to reclaim dead rows
  VACUUM contention can be an operational challenge
```

### Serializable (Strongest)

```
Serializable prevents all anomalies including write skew:

Write Skew Example:
  Doctor on-call system: must have at least 1 doctor on call
  Current: Alice on call, Bob on call

  Transaction 1 (Alice going off):     Transaction 2 (Bob going off):
    BEGIN;                               BEGIN;
    SELECT count(*) WHERE on_call = true;
    → 2  (both on call, safe to leave)  
                                          SELECT count(*) WHERE on_call = true;
                                          → 2 (also sees both on call)
    UPDATE SET on_call = false           
    WHERE doctor = 'Alice';              
                                          UPDATE SET on_call = false
                                          WHERE doctor = 'Bob';
    COMMIT;                              COMMIT;

  Result: 0 doctors on call! Both thought it was safe.
  → Write skew: the read and write sets don't overlap, so row-locking didn't help

Serializable prevents this:
  PostgreSQL Serializable Snapshot Isolation (SSI):
    Detects the dependency: T1 reads on_call count, T2 also reads on_call count
    Both write in a way that invalidates what the other read
    → One transaction aborted with serialization failure → retry
```

---

## How Isolation is Implemented

### Locking (Pessimistic)

```
Two-Phase Locking (2PL):
  Acquire all locks before any release
  Growing phase: acquire locks
  Shrinking phase: release locks (no new acquisitions)

  Shared lock (S):  readers hold S locks, compatible with other S
  Exclusive lock (X): writers hold X locks, incompatible with any other lock

  SELECT FOR UPDATE:  acquires X lock on rows read
  → Prevents concurrent writes until transaction commits
  → High contention → deadlocks possible → DB detects and aborts one

SELECT stock FROM product WHERE id = 123 FOR UPDATE;
  → Row 123 is X-locked until this transaction commits
  → Other transactions wanting to write row 123 will block
```

### MVCC (Optimistic)

```
Multi-Version Concurrency Control:
  Write a new version of the row without locking the old version
  Readers always see a consistent snapshot
  No read-write contention

  On conflict detection (Serializable):
    Track which transactions read which version ranges
    On commit: if another transaction has written a version we read → abort + retry

PostgreSQL uses MVCC for all isolation levels
MySQL InnoDB uses MVCC for Repeatable Read and below
SQL Server uses both MVCC (with SNAPSHOT isolation) and locking
```

---

## Isolation Levels in Cloud Databases

```
Database              Default Level    Max Level        Implementation
───────────────────────────────────────────────────────────────────
PostgreSQL            Read Committed   Serializable     MVCC + SSI
MySQL InnoDB          Repeatable Read  Serializable     MVCC + 2PL
Oracle                Read Committed   Serializable     MVCC
SQL Server            Read Committed   Serializable     Locking + SNAPSHOT
MongoDB (multi-doc)   Snapshot         Snapshot         MVCC
CockroachDB           Serializable     Serializable     Distributed MVCC
Google Spanner        Serializable     Serializable     TrueTime + 2PL
DynamoDB Txns         Serializable     Serializable     OCC (optimistic)
```

---

## Interview Quick Answers

- **What isolation level does PostgreSQL use by default?** — Read Committed. Most production apps run here. Use Repeatable Read or Serializable only when you need snapshot consistency or prevent write skew.
- **What is write skew?** — Two transactions read overlapping data, make non-overlapping writes, creating an invariant violation. Example: two doctors both go off-call because each saw the other still on-call. Only Serializable prevents this.
- **How does MVCC help performance?** — Readers don't block writers, writers don't block readers. Concurrent reads and writes can proceed simultaneously. High concurrency for OLTP workloads.
- **When would you use SELECT FOR UPDATE?** — When you read-then-write based on a value and need to prevent concurrent modifications. Example: decrement inventory only if stock > 0.
