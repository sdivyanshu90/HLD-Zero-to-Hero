# Module 04: Database Fundamentals and CAP Theorem

## Overview

Every system design decision about data storage ultimately comes down to three questions: what consistency guarantees do you need, how much availability can you sacrifice, and how much latency is acceptable? This module gives you the vocabulary and framework to answer them.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│             MODULE 04 LEARNING MAP                              │
│                                                                  │
│  01-rdbms-vs-nosql                                              │
│     └── SQL tables vs KV, Document, Wide-Column, Graph         │
│         When to use each; polyglot persistence                 │
│                    │                                            │
│                    ▼                                            │
│  02-cap-theorem                                                 │
│     └── C, A, P definitions; why P is not optional             │
│         CP vs AP trade-off with real database examples         │
│                    │                                            │
│                    ▼                                            │
│  03-pacelc-theorem                                              │
│     └── Extends CAP: latency vs consistency in normal ops      │
│         Google Spanner, Cassandra, DynamoDB in PACELC framework│
│                    │                                            │
│                    ▼                                            │
│  04-acid-vs-base                                                │
│     └── ACID: Atomicity, Consistency, Isolation, Durability    │
│         BASE: Basically Available, Soft State, Eventual        │
│         CRDTs, vector clocks, conflict resolution              │
│                    │                                            │
│                    ▼                                            │
│  05-isolation-levels                                            │
│     └── Read Committed → Repeatable Read → Serializable        │
│         MVCC internals, SELECT FOR UPDATE, write skew          │
└────────────────────────────────────────────────────────────────┘
```

---

## The Database Decision Framework

```
Step 1: What are your consistency requirements?
  Need ACID transactions (financial, inventory)?  → RDBMS
  Eventual consistency acceptable?               → NoSQL (AP)
  Strong consistency + global scale?             → Spanner/CockroachDB

Step 2: What is your data model?
  Tabular with relationships?         → PostgreSQL, MySQL
  Hierarchical / document-like?       → MongoDB, Firestore
  High-volume append / time-series?   → Cassandra, InfluxDB
  Graph relationships?                → Neo4j, Neptune
  Simple key-value?                   → Redis, DynamoDB

Step 3: What are your scale requirements?
  < 10K req/s, moderate data?         → Single RDBMS is fine
  > 100K req/s, multi-region writes?  → NoSQL or NewSQL

Step 4: What is your query pattern?
  Complex ad-hoc analytics?           → RDBMS or ClickHouse
  Known access patterns only?         → Cassandra (design table per query)
  Full-text search?                   → Elasticsearch
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-rdbms-vs-nosql.md](01-rdbms-vs-nosql.md) | SQL vs NoSQL families, when to use each |
| [02-cap-theorem.md](02-cap-theorem.md) | CAP theorem, CP vs AP, real examples |
| [03-pacelc-theorem.md](03-pacelc-theorem.md) | PACELC, Spanner, consistency spectrum |
| [04-acid-vs-base.md](04-acid-vs-base.md) | ACID/BASE, CRDTs, conflict resolution |
| [05-isolation-levels.md](05-isolation-levels.md) | Isolation levels, MVCC, write skew |
| [06-checkpoint.md](06-checkpoint.md) | Self-test questions |
