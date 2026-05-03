# HLD Zero to Hero

> A structured, first-principles curriculum for mastering High-Level System Design —  
> from hardware physics to distributed consensus to interview-ready problem walkthroughs.

---

## Repository Map

```
HLD-Zero-to-Hero/
│
├── modules/                        ← Theory curriculum (study in order)
│   ├── 01-hardware-and-physics-limits/
│   ├── 02-networking-protocols-and-api-paradigms/
│   ├── 03-core-infrastructure-and-traffic-routing/
│   ├── 04-database-fundamentals-and-cap-theorem/
│   ├── 05-database-internals-and-storage-engines/
│   ├── 06-scaling-and-partitioning/
│   ├── 07-replication-and-consensus/
│   ├── 08-caching-strategies/
│   ├── 09-asynchronous-processing-and-messaging/
│   ├── 10-microservices-resilience-and-security/
│   ├── 11-interview-framework-and-boe-math/
│   └── 12-project-bank-and-read-loop/
│
├── problems/                       ← Design walkthroughs by difficulty
│   ├── easy/
│   │   ├── url-shortener/
│   │   ├── distributed-cache/
│   │   └── distributed-id-generator/
│   ├── medium/
│   │   ├── distributed-rate-limiter/
│   │   ├── notification-system/
│   │   ├── realtime-chat-system/
│   │   ├── ticket-booking-system/
│   │   └── twitter-newsfeed/
│   └── hard/
│       ├── ad-click-aggregation/
│       ├── collaborative-text-editor/
│       ├── distributed-file-storage/
│       ├── distributed-web-crawler/
│       ├── food-delivery-platform/
│       ├── metrics-monitoring-and-alerting/
│       ├── payment-ledger-platform/
│       ├── realtime-multiplayer-game-backend/
│       ├── search-autocomplete/
│       ├── service-discovery-and-config/
│       ├── uber-ride-sharing/
│       └── video-streaming-platform/
│
└── solutions/                      ← Python implementations
    ├── easy/
    ├── medium/
    └── hard/
```

---

## Learning Path

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 1 — FOUNDATIONS                        │
│                        (Modules 01 – 05)                            │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────┤
│  Module 01   │  Module 02   │  Module 03   │  Module 04   │ Mod 05  │
│  Hardware &  │  Networking  │  Infra &     │  DB Fund. &  │  DB     │
│  Physics     │  Protocols & │  Traffic     │  CAP Theorem │ Intern. │
│  Limits      │  API Para.   │  Routing     │              │         │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     PHASE 2 — DISTRIBUTED SYSTEMS                   │
│                        (Modules 06 – 10)                            │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────┤
│  Module 06   │  Module 07   │  Module 08   │  Module 09   │ Mod 10  │
│  Scaling &   │  Replication │  Caching     │  Async Proc. │ Micro-  │
│  Partition.  │  & Consensus │  Strategies  │  & Messaging │ services│
└──────────────┴──────────────┴──────────────┴──────────────┴─────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     PHASE 3 — INTERVIEW PREP                        │
│                        (Modules 11 – 12 + Problems)                 │
├──────────────────────────┬──────────────────────────────────────────┤
│  Module 11               │  Module 12                               │
│  Interview Framework     │  Project Bank & R.E.A.D. Loop            │
│  + BoE Math              │  (20 system cheat sheets)                │
└──────────────────────────┴──────────────────────────────────────────┘
                                      │
                                      ▼
                  ┌─────────────────────────────────┐
                  │       problems/  +  solutions/   │
                  │  20 full walkthroughs, each:     │
                  │  01-requirements.md              │
                  │  02-traffic & capacity           │
                  │  03-API design                   │
                  │  04-core data structures         │
                  │  05-key algorithm / tradeoff     │
                  │  06-scaling & caching            │
                  │  07-failure modes                │
                  │  08-checkpoint Q&A               │
                  │  solution.py                     │
                  └─────────────────────────────────┘
```

---

## Module Curriculum

### Phase 1 — Foundations

| # | Module | Key Topics | Checkpoint Focus |
|---|--------|-----------|-----------------|
| 01 | [Hardware & Physics Limits](modules/01-hardware-and-physics-limits/README.md) | CPU cache hierarchy, latency numbers, throughput vs latency, data locality | Recite L1/L2/RAM/SSD/network latencies from memory |
| 02 | [Networking & API Paradigms](modules/02-networking-protocols-and-api-paradigms/README.md) | OSI L4/L7, TCP vs UDP, HTTP/1.1/2/3, REST vs gRPC vs GraphQL, WebSockets, SSE | Choose the right protocol for 5 different scenarios |
| 03 | [Infra & Traffic Routing](modules/03-core-infrastructure-and-traffic-routing/README.md) | Load balancers, routing algorithms, reverse proxies, API gateways, CDNs | Draw a full request path from user to database |
| 04 | [DB Fundamentals & CAP](modules/04-database-fundamentals-and-cap-theorem/README.md) | RDBMS vs NoSQL, CAP theorem, PACELC, ACID vs BASE, isolation levels | Pick the right DB + isolation level for 3 use-cases |
| 05 | [DB Internals & Storage](modules/05-database-internals-and-storage-engines/README.md) | B-Trees, LSM-Trees, write path, compaction, Bloom filters, engine selection | Explain when to choose LSM vs B-Tree and why |

### Phase 2 — Distributed Systems

| # | Module | Key Topics | Checkpoint Focus |
|---|--------|-----------|-----------------|
| 06 | [Scaling & Partitioning](modules/06-scaling-and-partitioning/README.md) | Vertical vs horizontal, sharding strategies, consistent hashing, virtual nodes, rebalancing | Design a sharding scheme for a 10 TB write-heavy table |
| 07 | [Replication & Consensus](modules/07-replication-and-consensus/README.md) | Leader/follower, multi-leader, leaderless, quorum math, split-brain, Raft/Paxos basics | Calculate quorum for 5-node cluster; describe leader election |
| 08 | [Caching Strategies](modules/08-caching-strategies/README.md) | Cache tiers, write-through/behind/around, eviction policies (LRU, LFU, ARC), cache stampede | Design a multi-tier cache for a social feed |
| 09 | [Async Processing & Messaging](modules/09-asynchronous-processing-and-messaging/README.md) | Message queues, Kafka internals, pub/sub, consumer groups, at-least/exactly-once delivery | Explain offset management and partition assignment |
| 10 | [Microservices, Resilience & Security](modules/10-microservices-resilience-and-security/README.md) | Service mesh, circuit breaker, bulkhead, rate limiting, mTLS, JWT, OAuth2 | Design a resilient microservice with all failure-mode patterns |

### Phase 3 — Interview Readiness

| # | Module | Key Topics | Checkpoint Focus |
|---|--------|-----------|-----------------|
| 11 | [Interview Framework & BoE Math](modules/11-interview-framework-and-boe-math/README.md) | R.E.A.D. framework, capacity estimation, QPS/storage math, common mistake patterns | Run BoE math for any of the 20 problems in < 3 min |
| 12 | [Project Bank & R.E.A.D. Loop](modules/12-project-bank-and-read-loop/README.md) | 20 system cheat sheets, bottleneck patterns, scale numbers, revision loop | Whiteboard any cheat-sheet system from memory |

---

## Latency Cheat Sheet

```
Operation                          Latency        Relative
─────────────────────────────────────────────────────────────────────
L1 cache hit                         0.5 ns        1×
Branch misprediction                   5 ns        10×
L2 cache hit                           7 ns        14×
Mutex lock/unlock                     25 ns        50×
RAM access (main memory)             100 ns       200×
Compress 1 KB with Snappy          3,000 ns     6,000×
Send 1 KB over 1 Gbps network      10,000 ns    20,000×
Read 4 KB randomly from SSD       150,000 ns   300,000×
Read 1 MB sequentially from RAM   250,000 ns   500,000×
Round trip within same datacenter 500,000 ns         ~0.5 ms
Read 1 MB sequentially from SSD  1,000,000 ns        ~1   ms
Disk seek (HDD)                  10,000,000 ns       ~10  ms
Read 1 MB sequentially from HDD  30,000,000 ns       ~30  ms
Send packet CA → Netherlands     150,000,000 ns      ~150 ms
─────────────────────────────────────────────────────────────────────
Rule of thumb:  RAM ~100 ns  |  SSD ~100 µs  |  HDD ~10 ms  |  WAN ~150 ms
```

---

## BoE Quick Reference

```
POWERS OF 10
─────────────────────────────────────────────
1 K   =  10^3     1 M   =  10^6     1 B  =  10^9
1 KB  =  10^3 B   1 MB  =  10^6 B   1 GB =  10^9 B   1 TB = 10^12 B

TIME CONVERSIONS
─────────────────────────────────────────────
1 day   =  86,400 s  ≈  10^5 s
1 month ≈  2.6 × 10^6 s
1 year  ≈  3.1 × 10^7 s

COMMON QPS ESTIMATES
─────────────────────────────────────────────
1 M requests/day  →  ~12 req/s   (low traffic)
10 M/day          →  ~115 req/s  (medium)
100 M/day         →  ~1,150 req/s
1 B/day           →  ~11,500 req/s  (large scale)

STORAGE SIZING
─────────────────────────────────────────────
1 tweet (text)  ≈  300 bytes
1 user record   ≈  1 KB
1 photo         ≈  300 KB
1 short video   ≈  30 MB
1 HD video (1h) ≈  1–2 GB
```

---

## CAP Theorem Visual

```
           Consistency
               /\
              /  \
             /    \
            /  CA  \   ← Impossible under partition
           /        \
          /          \
    CP   /────────────\   AP
        /              \
       /                \
      ──────────────────
   Partition Tolerance

  CP systems (choose C + P):   HBase, Zookeeper, etcd, Consul
  AP systems (choose A + P):   Cassandra, CouchDB, DynamoDB (default)
  CA systems (theoretical):    Single-node RDBMS (no partition)

  PACELC adds: when no Partition → trade-off between Latency and Consistency
    EL: lower latency → weaker consistency (DynamoDB eventual)
    EC: stronger consistency → higher latency (Spanner, CockroachDB)
```

---

## Design Problem Bank

### Easy — 30–45 min

| Project | Core Challenge | Key Tech |
|---------|---------------|---------|
| [URL Shortener](problems/easy/url-shortener/README.md) | Hash collision, redirect caching | Base62, Redis, Postgres |
| [Distributed Cache](problems/easy/distributed-cache/README.md) | Eviction, consistent hashing | LRU/LFU, Redis Cluster |
| [Distributed ID Generator](problems/easy/distributed-id-generator/README.md) | Clock skew, sequence overflow | Snowflake 64-bit layout |

### Medium — 45–60 min

| Project | Core Challenge | Key Tech |
|---------|---------------|---------|
| [Distributed Rate Limiter](problems/medium/distributed-rate-limiter/README.md) | Distributed counters, race conditions | Redis + Lua, token bucket |
| [Notification System](problems/medium/notification-system/README.md) | Fan-out at scale, channel routing | Kafka, FCM/APNs/SES |
| [Realtime Chat System](problems/medium/realtime-chat-system/README.md) | Message ordering, presence, group fan-out | WebSockets, Cassandra |
| [Ticket Booking System](problems/medium/ticket-booking-system/README.md) | Seat contention, double-booking prevention | Optimistic lock, Saga |
| [Twitter Newsfeed](problems/medium/twitter-newsfeed/README.md) | Fan-out write vs read, celebrity problem | Redis sorted sets, hybrid |

### Hard — 60 min

| Project | Core Challenge | Key Tech |
|---------|---------------|---------|
| [Ad Click Aggregation](problems/hard/ad-click-aggregation/README.md) | Exactly-once counting, late events | Kafka, Flink, Lambda arch |
| [Collaborative Text Editor](problems/hard/collaborative-text-editor/README.md) | Concurrent edits, conflict resolution | OT / CRDT, WebSockets |
| [Distributed File Storage](problems/hard/distributed-file-storage/README.md) | Chunking, deduplication, delta sync | SHA-256, S3, Rabin CDC |
| [Distributed Web Crawler](problems/hard/distributed-web-crawler/README.md) | URL dedup, politeness, spider traps | Bloom filter, Kafka frontier |
| [Food Delivery Platform](problems/hard/food-delivery-platform/README.md) | Order state machine, dispatch, ETA | Geo index, Saga, Redis |
| [Metrics & Alerting](problems/hard/metrics-monitoring-and-alerting/README.md) | Cardinality explosion, downsampling | Prometheus, M3DB, Gorilla |
| [Payment Ledger](problems/hard/payment-ledger-platform/README.md) | Double-entry, idempotency, isolation | Postgres SERIALIZABLE |
| [Multiplayer Game Backend](problems/hard/realtime-multiplayer-game-backend/README.md) | Lag compensation, cheat prevention | UDP, client prediction |
| [Search Autocomplete](problems/hard/search-autocomplete/README.md) | Pre-computed top-K, trie sharding | Redis, Rabin, CDN cache |
| [Service Discovery & Config](problems/hard/service-discovery-and-config/README.md) | Leader election, watch streams, CP | Raft, etcd/Consul |
| [Uber Ride Sharing](problems/hard/uber-ride-sharing/README.md) | Geospatial matching, surge pricing | Geohash/H3, Redis GEO |
| [Video Streaming](problems/hard/video-streaming-platform/README.md) | Transcoding pipeline, adaptive bitrate | FFmpeg, HLS, CDN |

---

## Problem Walkthrough Format

Every problem in `problems/` follows this 8-file structure:

```
{project}/
├── README.md                       ← Problem statement + architecture ASCII diagram
├── 01-requirements.md              ← Functional + non-functional + scope decisions
├── 02-{traffic-or-data-model}.md   ← BoE math: QPS, storage, bandwidth
├── 03-{api-or-flow}.md             ← API surface, request/response, protocols
├── 04-{core-data-structure}.md     ← Schema, data model, key algorithms
├── 05-{key-mechanism}.md           ← The hardest sub-problem (deep dive)
├── 06-{scaling-or-caching}.md      ← Horizontal scale, caching layers
├── 07-{failure-modes}.md           ← Failure scenarios + recovery strategies
└── 08-checkpoint.md                ← 5 interview Q&A with deep-dive answers
```

---

## Interview Framework (R.E.A.D.)

```
┌─────────────────────────────────────────────────────────────────┐
│  R  — Requirements          (5 min)                             │
│       Clarify functional requirements                           │
│       Nail down scale: DAU, QPS, storage, latency SLA           │
│       Agree on what's in scope / out of scope                   │
├─────────────────────────────────────────────────────────────────┤
│  E  — Estimation            (3 min)                             │
│       QPS = daily_requests / 86,400                             │
│       Storage = daily_writes × record_size × retention_days     │
│       Bandwidth = peak_QPS × avg_response_size                  │
├─────────────────────────────────────────────────────────────────┤
│  A  — Architecture          (15 min)                            │
│       Draw the happy path (write path + read path)              │
│       Identify the hardest sub-problem                          │
│       Justify every component you add                           │
├─────────────────────────────────────────────────────────────────┤
│  D  — Deep Dive             (15 min)                            │
│       Go deep on the hardest part                               │
│       Discuss 2–3 trade-offs explicitly                         │
│       Address failure modes and recovery                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Suggested Study Schedule

```
Week 1 — Theory Foundation
─────────────────────────────────────────────────────────────
Day 1  │  Module 01 (Hardware)    + Module 02 (Networking)
Day 2  │  Module 03 (Infra)       + Module 04 (DB + CAP)
Day 3  │  Module 05 (DB Internals)+ Module 06 (Scaling)
Day 4  │  Module 07 (Replication) + Module 08 (Caching)
Day 5  │  Module 09 (Async/Kafka) + Module 10 (Microservices)
Day 6  │  Module 11 (Framework)   + Module 12 (Project Bank)
Day 7  │  Full revision: latency table, CAP/PACELC, quorum math

Week 2 — Easy + Medium Problems
─────────────────────────────────────────────────────────────
Day 8  │  URL Shortener + Distributed Cache
Day 9  │  Distributed ID Generator + Rate Limiter
Day 10 │  Notification System + Twitter Newsfeed
Day 11 │  Realtime Chat + Ticket Booking
Day 12 │  Whiteboard drill: all 5 medium problems cold

Week 3 — Hard Problems
─────────────────────────────────────────────────────────────
Day 13 │  Ad Click Aggregation + Distributed Web Crawler
Day 14 │  Search Autocomplete + Collaborative Text Editor
Day 15 │  Distributed File Storage + Video Streaming
Day 16 │  Payment Ledger + Service Discovery
Day 17 │  Uber Ride Sharing + Food Delivery + Multiplayer Game
Day 18 │  Metrics & Alerting — all hard problems review

Week 4 — Mock Interviews
─────────────────────────────────────────────────────────────
Day 19+ │  1 timed problem per day (45-60 min), no notes
         │  Record yourself and review for missed trade-offs
         │  Focus: BoE math in < 3 min, draw architecture first
```

---

## Mastery Checklist

For each module, you pass when you can do **all** of the following without notes:

```
□  Define every core concept precisely (no hand-waving)
□  Give a real-world analogy for the concept
□  State the 2–3 most important trade-offs
□  Describe at least 2 failure modes and how to recover
□  Apply the concept to a novel design scenario
□  Answer the module checkpoint in < 5 minutes
```

For each problem, you pass when you can:

```
□  Derive requirements and BoE numbers from scratch (< 5 min)
□  Draw the complete architecture diagram (write + read paths)
□  Identify and deeply explain the hardest sub-problem
□  Compare at least 2 alternative approaches with explicit trade-offs
□  Answer all 5 checkpoint questions clearly
□  Complete the full design in ≤ 45 min (easy) / 60 min (hard)
```

---

## Key Trade-Off Patterns

```
CONSISTENCY vs AVAILABILITY
  Need exact counts (billing, payments) → CP, SERIALIZABLE, Postgres
  Can tolerate stale reads (social feed, cache) → AP, eventual, Cassandra

LATENCY vs DURABILITY
  Hot path (< 10ms) → Redis cache, in-memory, skip disk
  Durable events (audit, billing) → Kafka, fsync, WAL

FAN-OUT WRITE vs FAN-OUT READ
  Low follower count → fan-out on write (precompute timelines)
  Celebrity / viral → fan-out on read (pull on query)
  Hybrid → fan-out write for normal users, read for high-follower

NORMALIZATION vs DENORMALIZATION
  Write-heavy, complex queries → normalize (3NF, Postgres)
  Read-heavy, fixed access patterns → denormalize (Cassandra, DynamoDB)

PUSH vs PULL
  Server pushes state → WebSockets, SSE (chat, live scores)
  Client polls server → REST polling (acceptable for low-frequency)
  Event-driven → Kafka, message queue (decoupled, async)
```

---

## Solutions Index

All Python implementations live in `solutions/`:

```
solutions/
├── easy/
│   ├── url-shortener/solution.py           ← Base62 encode, TTL cache, redirect
│   ├── distributed-cache/solution.py       ← LRU + consistent hashing simulation
│   └── distributed-id-generator/solution.py← Snowflake ID: timestamp+node+seq
├── medium/
│   ├── distributed-rate-limiter/solution.py← Token bucket + sliding window
│   ├── notification-system/solution.py     ← Fan-out, channel routing, retry
│   ├── realtime-chat-system/solution.py    ← Message store, WS session map
│   ├── ticket-booking-system/solution.py   ← Optimistic lock, saga pattern
│   └── twitter-newsfeed/solution.py        ← Hybrid fan-out, timeline cache
└── hard/
    ├── ad-click-aggregation/solution.py    ← Tumbling window, dedup, idempotency
    ├── collaborative-text-editor/solution.py← OT transform, CRDT RGA
    ├── distributed-file-storage/solution.py ← Rabin CDC, SHA-256 content-addr
    ├── distributed-web-crawler/solution.py  ← URL frontier, bloom filter
    ├── food-delivery-platform/solution.py   ← Order FSM, geo dispatch
    ├── metrics-monitoring-and-alerting/solution.py← Gorilla XOR, alert eval
    ├── payment-ledger-platform/solution.py  ← Double-entry, idempotency key
    ├── realtime-multiplayer-game-backend/solution.py← Client predict, lag comp
    ├── search-autocomplete/solution.py      ← Trie, top-K pre-compute
    ├── service-discovery-and-config/solution.py← Raft election, health check
    ├── uber-ride-sharing/solution.py        ← Geohash index, surge pricing
    └── video-streaming-platform/solution.py ← Transcoding DAG, HLS segments
```

---

> **Start here:** [Module 01 — Hardware and Physics Limits](modules/01-hardware-and-physics-limits/README.md)  
> **Jump to problems:** [problems/](problems/README.md)  
> **See implementations:** [solutions/](solutions/README.md)
