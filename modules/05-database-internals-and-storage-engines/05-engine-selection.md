# Storage Engine Selection

## How to Choose: B-Tree vs LSM vs Column vs Specialized

The storage engine is the most fundamental architectural choice for a database system. Different engines make irreconcilable trade-offs.

---

## Decision Framework

```
┌─────────────────────────────────────────────────────────────────┐
│               STORAGE ENGINE SELECTION FRAMEWORK                 │
│                                                                   │
│  Step 1: What is the dominant operation?                         │
│    Reads >> Writes?  → B-Tree (read-optimized)                  │
│    Writes >> Reads?  → LSM Tree (write-optimized)               │
│    OLAP queries?     → Columnar store                           │
│                                                                   │
│  Step 2: What are the access patterns?                          │
│    Point lookups by key?  → B-Tree or KV (hash index)           │
│    Range scans?           → B-Tree or LSM (sorted)              │
│    Analytical aggregates? → Columnar (scan one column)          │
│    Time-series?           → LSM with TWCS or InfluxDB           │
│                                                                   │
│  Step 3: Consistency requirements?                              │
│    ACID transactions?     → B-Tree (PostgreSQL, MySQL)          │
│    Eventual OK?           → LSM (Cassandra, RocksDB)            │
│    Time-series only?      → Specialized (InfluxDB, TimescaleDB)  │
│                                                                   │
│  Step 4: Scale?                                                  │
│    Single node (≤ 10TB)?  → B-Tree RDBMS fine                  │
│    Multi-node (distributed)? → LSM-based NoSQL                  │
│    Huge analytical scans? → Columnar (Parquet, ClickHouse)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Storage Engine Comparison Matrix

```
Engine Type         Read    Write   Range   Space   Complexity  Use Case
──────────────────────────────────────────────────────────────────────────────
B-Tree (Postgres)   ●●●●    ●●●     ●●●●    ●●●●    Low         OLTP, CRUD
LSM (Cassandra)     ●●●     ●●●●●   ●●●     ●●●     Medium      High-write, append
Columnar (Parquet)  ●●●●●   ●●      ●●      ●●●●●   Medium      OLAP analytics
Hash Index (RAM)    ●●●●●   ●●●●●   ✗       ●●      Low         Cache, KV store
Full-text (ES)      ●●●●    ●●●     ●●      ●●      High        Search
Graph (Neo4j)       ●●●     ●●●     ●●      ●●      High        Relationship traversal
Time-series (Flux)  ●●●●    ●●●●    ●●●●    ●●●●●   Medium      Metrics, IoT
```

---

## B-Tree Engines: PostgreSQL vs MySQL InnoDB

```
PostgreSQL:
  Engine: custom heap-based with B-tree indexes
  MVCC: complete multi-version, no undo log needed per row
  Vacuum: background process to reclaim dead row versions
  Best for: complex queries, advanced types (JSONB, arrays, ranges)
            PostGIS (geospatial), full-text search, OLTP+light OLAP

MySQL InnoDB:
  Engine: B+ tree clustered by primary key
  MVCC: undo log for old versions
  Clustered PK: data stored in PK order → fast PK lookups
  Best for: high-concurrency reads, simple CRUD, tight integration with MySQL ecosystem

MongoDB (document + B-tree):
  Engine: WiredTiger (B-tree by default, LSM optional)
  MVCC: since MongoDB 4.0
  Best for: flexible schema, JSON documents, moderate OLTP
```

---

## LSM Engines: RocksDB vs Cassandra vs LevelDB

```
RocksDB (Facebook):
  Embeddable KV store (used as engine inside other systems)
  Highly configurable compaction, compression, bloom filters
  Used by: MyRocks (MySQL), CockroachDB, TiKV, Kafka log storage
  Best for: embedded storage in custom systems, high-write KV

Apache Cassandra:
  Distributed wide-column database
  LSM tree per node, configurable compaction strategy
  Tunable consistency (ONE → QUORUM → ALL)
  Best for: high write throughput, multi-datacenter, time-series, always-on

HBase (Apache):
  Distributed wide-column (Bigtable-inspired)
  HDFS-backed storage (uses HDFS for durability)
  Strong consistency (ZooKeeper coordination)
  Best for: Hadoop ecosystem, large analytical + OLTP hybrid
```

---

## Columnar Engines: When Analytical Queries Dominate

```
Row store (PostgreSQL page):
  Row 1: [id=1][name="Alice"][age=30][country="US"][revenue=1000]
  Row 2: [id=2][name="Bob"][age=25][country="UK"][revenue=2000]
  ...
  Query: SELECT SUM(revenue) FROM users → reads ALL columns per row!

Columnar store (Parquet/ORC file):
  id column:      [1][2][3][4]...[1B]
  name column:    ["Alice"]["Bob"]...  (not read for revenue sum!)
  age column:     [30][25]...          (not read!)
  country column: [US][UK]...          (possibly read for filter)
  revenue column: [1000][2000]...      ← only this column read!

  SUM(revenue): read 1B × 4 bytes = 4 GB
  vs row store: read 1B × 100 bytes = 100 GB
  → 25× less I/O for this analytical query!

Additionally: columnar data compresses much better:
  Revenue column: [1000][2000][1500][2000][1000]... → many repeated values
  Dictionary encoding: {A:1000, B:1500, C:2000} → [A][C][B][C][A]... → tiny!
  Typical compression: 5-10× better than row store for analytical data
```

### Columnar Engines in Practice

```
Apache Parquet / ORC:
  File format (not a database) used by Spark, Hive, Presto, BigQuery
  Row groups of ~128MB, column chunks within each group
  Predicate pushdown: skip row groups whose min/max doesn't match filter
  Used by: data lakes (S3 + Parquet = standard data lake format)

ClickHouse:
  Columnar OLAP database
  MergeTree engine: LSM-inspired merge, columnar storage
  Vectorized query execution (SIMD operations on column arrays)
  Excellent for: web analytics, clickstream, log analysis (100B+ row queries in seconds)

Apache Druid:
  Real-time columnar OLAP
  Pre-aggregation during ingestion → sub-second aggregate queries
  Used by: Netflix, Airbnb, Lyft for real-time dashboards

BigQuery / Redshift / Snowflake:
  Managed cloud columnar warehouses
  Separate compute and storage
  BigQuery: serverless, Dremel execution engine, Capacitor columnar format
```

---

## Specialized Engines

### Time-Series Databases

```
Time-series data characteristics:
  - Timestamps are always appended (never go back in time)
  - Queries are typically: "last N values for metric X" or "aggregate in time range"
  - High cardinality: millions of unique metric label combinations

InfluxDB / Prometheus:
  Custom TSM (Time Structured Merge) engine
  Inverted index on tags for fast label lookup
  Automatic data retention policies (drop old data automatically)
  Best for: infrastructure metrics, IoT sensor data

TimescaleDB:
  PostgreSQL extension
  Automatic time-based hypertable partitioning
  Native PostgreSQL SQL, JOIN with other tables
  Best for: SQL-savvy teams needing time-series + relational data

Cassandra + TWCS:
  Excellent for high-write time-series when already using Cassandra
  TWCS drops entire SSTables when their time window expires
```

---

## Real-World Storage Engine Decisions

```
System            Storage Engine     Reason
──────────────────────────────────────────────────────────────
Twitter timeline  Manhattan (FB-inspired LSM)   High write (tweets), geo-distributed
WhatsApp messages Mnesia + Cassandra   Erlang native + scalable persistence
GitHub repos      Git object store    Content-addressed, append-only by design
Uber trips DB     Schemaless (MySQL→Cassandra)   Outgrew single MySQL, migrated to Cassandra
Netflix streaming DynamoDB             Low-latency reads, high availability
Stripe payments   PostgreSQL          ACID required for financial transactions
Datadog metrics   InfluxDB / M3DB     Time-series, high cardinality
Elasticsearch doc Lucene segments (LSM-inspired)  Inverted index, text search
```

---

## Interview Quick Answers

- **Why does Cassandra use LSM and not B-tree?** — Cassandra's primary use case is high-write throughput (time-series, messaging, event logs). LSM converts all writes to sequential appends. B-tree requires random writes which are expensive. Cassandra accepts slightly slower reads in exchange for dramatically faster writes.
- **When would you use a columnar database instead of a row database?** — When the dominant query pattern is aggregating a few columns across many rows (OLAP). Row databases read entire rows even when you need only one column. Columnar databases only read the columns referenced in the query — 5-25× less I/O.
- **Why is PostgreSQL still used for high-write workloads despite using B-trees?** — PostgreSQL's WAL + group commit + large buffer pool makes it surprisingly write-efficient up to ~100K inserts/s. For >1M writes/s or distributed writes, LSM-based systems win.
