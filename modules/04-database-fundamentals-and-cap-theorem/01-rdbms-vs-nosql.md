# RDBMS vs NoSQL

## The Fundamental Choice

Relational (SQL) and non-relational (NoSQL) databases make fundamentally different trade-offs. Neither is universally better — the right choice depends on your data model, access patterns, and consistency requirements.

---

## Relational Databases (RDBMS)

RDBMS store data in tables with rows and columns, enforcing a strict schema and supporting SQL queries:

```
┌────────────────────────────────────────────────────────────────┐
│                   RELATIONAL DATA MODEL                         │
│                                                                  │
│  users table                  orders table                      │
│  ┌────┬──────────┬──────┐    ┌────┬─────────┬───────┐        │
│  │ id │  name    │email │    │ id │ user_id │amount │        │
│  ├────┼──────────┼──────┤    ├────┼─────────┼───────┤        │
│  │  1 │ Alice    │a@... │    │  1 │    1    │ $50   │        │
│  │  2 │ Bob      │b@... │    │  2 │    1    │ $120  │        │
│  │  3 │ Carol    │c@... │    │  3 │    2    │ $30   │        │
│  └────┴──────────┴──────┘    └────┴─────────┴───────┘        │
│                                                                  │
│  JOIN query:                                                    │
│  SELECT u.name, SUM(o.amount)                                   │
│  FROM users u JOIN orders o ON u.id = o.user_id                │
│  GROUP BY u.name                                                │
└────────────────────────────────────────────────────────────────┘
```

### RDBMS Strengths

```
1. ACID Transactions
   - Atomicity: all-or-nothing updates
   - Consistency: constraints always satisfied
   - Isolation: concurrent transactions don't interfere
   - Durability: committed data survives crashes

2. SQL: Expressive Query Language
   - Ad-hoc queries without schema changes
   - JOINs across tables
   - Aggregations, window functions, CTEs

3. Referential Integrity
   - Foreign keys enforce relationships
   - Cannot have orphaned child records

4. Normalization
   - One source of truth for each piece of data
   - Updates only need to happen in one place
```

### RDBMS Weaknesses

```
1. Scaling is Hard
   - Vertical scaling: buy bigger server (expensive, ceiling)
   - Horizontal sharding: complex, breaks JOINs across shards

2. Schema is Rigid
   - Schema changes require migrations (potentially table locks)
   - Adding a column to a 1-billion-row table: hours of downtime without online DDL

3. Object-Relational Impedance Mismatch
   - Application data is objects/nested structures
   - DB stores flat tables → ORM adds complexity and N+1 risk

4. Poor fit for:
   - Hierarchical/graph data (social graphs, file trees)
   - Schema-less or semi-structured data (user preferences, JSON blobs)
   - Write-heavy time-series data
   - Full-text search
```

---

## NoSQL Databases

NoSQL is an umbrella term for databases that don't use the relational model. Four main families:

### 1. Key-Value Stores

```
Model: dict[key] → value (opaque blob)
Examples: Redis, DynamoDB (as KV), Memcached

user:1234 → {"name":"Alice","email":"alice@..","cart":[...]}

Strengths:
  ✓ O(1) read/write by key
  ✓ Extremely simple data model
  ✓ Horizontally scalable (partition by key)
  ✓ Sub-millisecond latency

Weaknesses:
  ✗ No query by value (must know key)
  ✗ No relationships between values
  ✗ Secondary indexes expensive or not supported

Use cases: session stores, caches, shopping carts, user preferences
```

### 2. Document Stores

```
Model: collections of JSON/BSON documents, each with its own schema
Examples: MongoDB, Firestore, DynamoDB, CouchDB

{
  "_id": "user:1234",
  "name": "Alice",
  "email": "alice@example.com",
  "preferences": {
    "theme": "dark",
    "notifications": {"email": true, "sms": false}
  },
  "recent_orders": [
    {"id": "ord:001", "amount": 50, "date": "2024-01-01"},
    {"id": "ord:002", "amount": 120, "date": "2024-01-15"}
  ]
}

Strengths:
  ✓ Natural mapping to application objects
  ✓ Schema-less (each document can differ)
  ✓ Rich queries on document fields
  ✓ Good for hierarchical/nested data

Weaknesses:
  ✗ No JOINs across collections (by design)
  ✗ Data duplication (denormalization required)
  ✗ Consistency trade-offs (eventual by default in many)

Use cases: user profiles, product catalogs, blog posts, configurations
```

### 3. Wide-Column Stores

```
Model: rows identified by key, columns can vary per row, organized in column families
Examples: Apache Cassandra, HBase, Bigtable

Row key: user:1234
  Column family "profile": {name: "Alice", email: "alice@.."}
  Column family "activity": {
    ts:2024-01-01: "login",
    ts:2024-01-02: "purchase",
    ts:2024-01-03: "logout"
  }

Key insight: designed for queries like "get all events for user X in time range"
The data is clustered by partition key (user) and sorted by clustering key (timestamp)

Strengths:
  ✓ Extremely scalable writes (append-only LSM tree)
  ✓ Efficient range scans on clustering key
  ✓ Tunable consistency (quorum levels)

Weaknesses:
  ✗ Query pattern must be known upfront (data model = query)
  ✗ No JOINs, limited secondary indexes
  ✗ No multi-row transactions (without Cassandra LWT)

Use cases: time-series, IoT sensor data, audit logs, chat history
```

### 4. Graph Databases

```
Model: nodes (entities) connected by edges (relationships)
Examples: Neo4j, Amazon Neptune, JanusGraph

(Alice) -[:FOLLOWS]-> (Bob)
(Alice) -[:LIKES]->   (Post:123)
(Bob)   -[:FOLLOWS]-> (Carol)
(Carol) -[:WORKS_AT]-> (Company:Acme)

Query: "Who does Alice follow who also works at Acme?"
  MATCH (alice:Person {name:"Alice"})-[:FOLLOWS]->(f)-[:WORKS_AT]->(c:Company {name:"Acme"})
  RETURN f.name

Strengths:
  ✓ Efficient relationship traversal (O(k) per hop, k = edge degree)
  ✓ Natural representation of networks, trees, hierarchies
  ✓ Pattern matching queries

Weaknesses:
  ✗ Harder to scale horizontally than KV/document stores
  ✗ Not suited for simple aggregate queries
  ✗ Niche use cases

Use cases: social graphs, fraud detection, recommendation engines, knowledge graphs
```

---

## Decision Matrix

```
                     Flexibility  Scalability  Consistency  Query Power
                     ──────────   ──────────   ──────────   ──────────
RDBMS (Postgres)     Low          Medium       High (ACID)  High (SQL)
Key-Value (Redis)    Low          Very High    Varies       Very Low
Document (MongoDB)   High         High         Medium       Medium
Wide-Column (Cass.)  Medium       Very High    Tunable      Medium (CQL)
Graph (Neo4j)        Medium       Medium       Medium       High (Cypher)
```

### When to Choose What

| Requirement | Database Choice |
|-------------|----------------|
| ACID transactions, complex queries | PostgreSQL, MySQL |
| Sub-ms read by key, ephemeral data | Redis, Memcached |
| Flexible JSON documents, rich queries | MongoDB, Firestore |
| High write throughput, time-series | Cassandra, InfluxDB |
| Full-text search | Elasticsearch, Solr |
| Graph traversal, fraud detection | Neo4j, Neptune |
| Analytics, OLAP | BigQuery, Redshift, ClickHouse |
| Multi-model (graph + document + KV) | ArangoDB, FaunaDB |

---

## Polyglot Persistence

Modern systems often use multiple database types:

```
E-commerce platform:
  PostgreSQL    → Orders, payments (ACID required)
  Redis         → Sessions, shopping cart (fast KV)
  Elasticsearch → Product search (full-text + faceting)
  MongoDB       → Product catalog (flexible schema)
  InfluxDB      → Metrics, analytics (time-series)
  Neo4j         → Product recommendations (graph)
```

---

## Interview Quick Answers

- **Why not use an RDBMS for everything?** — RDBMS scaling is hard: horizontal sharding breaks JOINs, schema changes are slow on large tables. For write-heavy, schema-less, or geographically distributed data, NoSQL trades consistency for scalability.
- **Why not use NoSQL for everything?** — NoSQL typically sacrifices ACID transactions, JOINs, and strong consistency. Financial transactions, inventory management, and any use case requiring complex queries across related data belongs in a relational DB.
- **What is the CAP theorem's effect on NoSQL?** — Most NoSQL databases partition-tolerant by design. When a network partition occurs, they choose availability (AP: Cassandra, DynamoDB) or consistency (CP: MongoDB w/ majority writes, HBase).
