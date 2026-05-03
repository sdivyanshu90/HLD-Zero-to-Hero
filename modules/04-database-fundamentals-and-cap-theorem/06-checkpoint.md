# Module 04 Checkpoint: Database Fundamentals and CAP Theorem

## Questions to Test Your Understanding

---

**Q1.** You're building an inventory system for e-commerce. A user should not be able to purchase an item if stock is 0. Which database type and isolation level do you choose?

> **Answer:** Relational database with REPEATABLE READ or SERIALIZABLE isolation. You need the read (stock check) and write (decrement) to be atomic. Use `SELECT ... FOR UPDATE` to hold an X-lock on the row, preventing concurrent decrement: `SELECT stock FROM inventory WHERE product_id=123 FOR UPDATE` then `UPDATE SET stock=stock-1 WHERE product_id=123 AND stock > 0`. A NoSQL/BASE database risks overselling during concurrent checkouts.

---

**Q2.** Cassandra nodes A, B, C are in a ring. A network partition splits {A} from {B, C}. A write arrives at B with QUORUM (2/3 needed). What happens?

> **Answer:** Write succeeds! B and C form a quorum (2 of 3). A is partitioned but the write can proceed. A will sync via anti-entropy (hinted handoff) when the partition heals. This is AP behavior: Cassandra remains available despite A being unreachable.

---

**Q3.** What is the difference between Serializable (SQL) and Linearizable (distributed systems)?

> **Answer:** Serializable means concurrent transactions appear to run in *some* serial order (even if that order doesn't match real-world clock order). Linearizable means operations appear to take effect at a single real-time point (respects wall clock ordering). Linearizability is stronger. Google Spanner achieves both using TrueTime.

---

**Q4.** Two users simultaneously book the last seat on a flight. You use an RDBMS. How do you prevent double booking?

> **Answer:** Use SERIALIZABLE isolation or an explicit lock:
> ```sql
> BEGIN;
> SELECT seats_remaining FROM flights WHERE id = 123 FOR UPDATE;
> -- check > 0 in application
> UPDATE flights SET seats_remaining = seats_remaining - 1 WHERE id = 123;
> INSERT INTO bookings (flight_id, user_id) VALUES (123, user_id);
> COMMIT;
> ```
> `FOR UPDATE` holds an exclusive lock on the flight row. The second transaction blocks until the first commits. Then it sees 0 seats and aborts.

---

**Q5.** Design a globally distributed "like" counter for a social media post. Choose: CP or AP? What trade-offs?

> **Answer:** AP (BASE, eventual consistency). Reasons:
> - Being slightly stale (showing 1,049 instead of 1,050 likes) is acceptable
> - Being unavailable during a partition (cannot like the post) is worse UX
> - Like counts are not financial — losing a few counts due to conflict resolution is tolerable
> 
> Implementation: Use a CRDT G-Counter. Each datacenter has its own slot. Total = sum. Merges are commutative, no conflicts. Cassandra COUNTER type does this.

---

## Key Concepts Checklist

- [ ] RDBMS: ACID, JOINs, normalized schema, SQL
- [ ] NoSQL families: KV, Document, Wide-Column, Graph — and when to use each
- [ ] CAP: Consistency vs Availability during partition; P is not optional
- [ ] CP examples: Zookeeper, etcd, HBase, MongoDB
- [ ] AP examples: Cassandra, DynamoDB, CouchDB, DNS
- [ ] PACELC: extends CAP to cover normal-operation latency vs consistency
- [ ] ACID: Atomicity, Consistency, Isolation, Durability — definitions and purpose
- [ ] BASE: Basically Available, Soft State, Eventually Consistent
- [ ] CRDT: conflict-free merge data structures (G-Counter, OR-Set)
- [ ] Isolation levels: Read Committed, Repeatable Read, Serializable
- [ ] MVCC: readers don't block writers; consistent snapshots
- [ ] Write skew: two transactions reading and writing non-overlapping data inconsistently
