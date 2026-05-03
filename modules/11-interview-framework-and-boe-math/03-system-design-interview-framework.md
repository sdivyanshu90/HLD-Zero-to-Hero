# System Design Interview Framework

## The RADIO Framework

A structured 5-step approach to any system design interview:

```
R - Requirements
A - API Design
D - Data Model
I - Infrastructure and High-Level Design
O - Optimizations and Trade-offs
```

---

## Step R: Requirements (5-10 minutes)

```
Clarify before designing. Never start coding/drawing immediately.

Functional Requirements (what the system does):
  → "What are the core features?" 
  Focus on top 3-5 features. Avoid scope creep.
  Example (URL shortener): shorten URL, redirect to original, analytics?

Non-Functional Requirements (how the system behaves):
  Scale:
    - DAU? Concurrent users?
    - QPS: read vs write? Read-heavy or write-heavy?
    - Data growth rate: how much per day/year?
  Availability:
    - Acceptable downtime? 99.9% (8.7h/year) vs 99.99% (52min/year)?
  Latency:
    - P99 latency requirement? <100ms? <1s?
  Consistency:
    - Strong or eventual? Can users see stale data?
  Durability:
    - Data loss acceptable? RPO? RTO?
  
  Typical defaults (state these to interviewer):
    - High availability (99.9%+)
    - Eventual consistency acceptable for most reads
    - Low latency (<100ms P99 for user-facing reads)
    - Horizontal scaling (design for growth)

Constraints to clarify:
  - Budget (bare metal vs cloud)?
  - Existing infrastructure?
  - New service or part of existing system?
```

---

## Step A: API Design (5 minutes)

```
Define the public interface before internal implementation:

URL Shortener API:
  POST /api/v1/urls
  Request:  {"long_url": "https://example.com/very/long/url", "custom_alias": "myalias"}
  Response: {"short_url": "https://bit.ly/abc123", "expires_at": "2025-01-01"}
  
  GET /{short_code}
  Response: HTTP 301 Redirect → Location: https://example.com/very/long/url
  
  GET /api/v1/urls/{short_code}/stats
  Response: {"clicks": 1234, "unique_visitors": 890, "countries": [...]}

API design principles:
  ✓ Use nouns, not verbs (REST): /urls, not /createUrl
  ✓ Version your API: /api/v1/ (can evolve without breaking clients)
  ✓ Appropriate HTTP methods: GET (read), POST (create), PUT/PATCH (update), DELETE (delete)
  ✓ Pagination for list endpoints: ?page=1&limit=20 or cursor-based
  ✓ Error responses: use HTTP status codes + error body {"error": "...", "code": "..."}
  ✓ For streaming: consider if REST, SSE, or WebSocket is appropriate
```

---

## Step D: Data Model (5-10 minutes)

```
Choose storage, then design schema:

1. Choose the right database(s):
   - Relational (user accounts, orders, financial data)? → PostgreSQL / MySQL
   - Document (flexible schema, user profiles)? → MongoDB
   - Wide-column (time-series, write-heavy)? → Cassandra / HBase
   - In-memory (caching, sessions, rate limiting)? → Redis
   - Search (full-text search, faceted search)? → Elasticsearch
   - Graph (social network, fraud detection)? → Neo4j
   - Object store (files, images, videos)? → S3/GCS

URL Shortener schema:
  urls table (PostgreSQL):
    short_code   VARCHAR(10) PRIMARY KEY
    long_url     TEXT NOT NULL
    user_id      BIGINT (FK to users)
    created_at   TIMESTAMP
    expires_at   TIMESTAMP
    is_active    BOOLEAN DEFAULT TRUE
    
    INDEX: (user_id) for "my URLs" queries
    INDEX: (expires_at) for cleanup jobs

  url_clicks table (Cassandra/ClickHouse for analytics):
    short_code   VARCHAR(10)
    clicked_at   TIMESTAMP
    ip_address   INET
    country      VARCHAR(2)
    referer      TEXT
    
    Partition key: short_code (range queries by time per URL)
    Clustering key: clicked_at DESC

Sizing the data:
  How many rows? Storage per row? Total storage? (Use BoE from previous file)
```

---

## Step I: Infrastructure and High-Level Design (15-20 minutes)

```
Draw the architecture:

  ┌──────────────────────────────────────────────────────────────┐
  │                    URL Shortener Architecture                  │
  │                                                                │
  │  Client ──▶ CDN (static assets) ──▶ API Gateway              │
  │                                           │                   │
  │                     ┌─────────────────────┤                   │
  │                     ▼                     ▼                   │
  │              URL Creation Service    Redirect Service         │
  │                     │                     │                   │
  │              ┌──────┤                ┌────┤                   │
  │              │  Write                │  Cache (Redis)         │
  │              ▼  Path                 ▼  short_code→long_url   │
  │         PostgreSQL DB           PostgreSQL DB                 │
  │         (Primary)               (Read Replica)               │
  │                                                               │
  │         Analytics Pipeline:                                   │
  │         Click event → Kafka → Stream Processor → Cassandra    │
  └──────────────────────────────────────────────────────────────┘

Components to discuss:
  1. Load balancer: L7 (routes /api/* to service, /{code} to redirect)
  2. App tier: stateless, horizontally scalable
  3. Cache: Redis for short_code → long_url (high read:write ratio)
  4. DB: primary for writes, replicas for reads
  5. CDN: for any static content
  6. Async processing: analytics via Kafka (don't block redirect on analytics)

Key design decisions to justify:
  - Why Redis? (URL lookup is read-heavy, O(1) key lookup)
  - Why PostgreSQL? (relational, ACID, flexible queries)
  - Why async analytics? (don't add latency to redirect path)
  - Why separate redirect service? (scale independently, very high QPS)
```

---

## Step O: Optimizations and Trade-offs (10 minutes)

```
Deep dive: address non-functional requirements

1. Scalability:
   - URL redirect: cache heavy → Redis cluster → 99%+ cache hit rate
   - DB: read replicas for read scaling, sharding by short_code if very large
   - Stateless app servers: horizontal scale behind load balancer

2. Availability:
   - Redis: master-replica with sentinel, or Redis Cluster
   - DB: primary-replica, automated failover (AWS RDS Multi-AZ)
   - Multiple availability zones: app servers + DBs in 2-3 AZs
   - Health checks + circuit breakers at load balancer

3. Latency:
   - Cache hit rate: URL redirect should be <5ms (Redis ~0.5ms + network)
   - CDN for global users: edge cache popular redirects at PoPs
   - Cache pre-warming: popular URLs cached proactively

4. Data consistency:
   - Write-through cache (write DB + update/invalidate cache atomically)
   - Cache expiry for eventual consistency (TTL = 24h)

5. Security:
   - Rate limit URL creation (prevent abuse)
   - Scan long URLs for malware/phishing
   - Require authentication for custom aliases

Trade-offs to present:
  - Redirects: 301 (permanent, browser caches → can't track) vs 302 (temporary, no cache → can track)
  - Strong vs eventual consistency: strong = every redirect shows latest → more DB load
  - Sharding by short_code vs user_id: code lookup is faster (no join), user queries require scatter-gather
```

---

## Common Interview Mistakes

```
✗ Jumping to solution without clarifying requirements
✗ Designing for a scale you didn't establish (over-engineering)
✗ Forgetting failure modes (what if Redis is down? DB fails?)
✗ Not explaining trade-offs ("I chose X because Y, trade-off is Z")
✗ Choosing complex architecture for simple problems
✗ Not asking about read vs write ratio (changes everything!)
✗ Forgetting: cache invalidation, data consistency, authentication
✗ Saying "blockchain" or "AI" without justification

✓ Narrate your thinking aloud
✓ Confirm your assumptions ("I'm assuming 100M DAU, does that sound right?")
✓ Say "I'd start simple and scale as needed"
✓ Know your bottlenecks (usually DB writes or network bandwidth)
```

---

## Interview Quick Answers

- **What should you do first in a system design interview?** — Clarify requirements: functional (what features) and non-functional (scale, latency, availability). Estimate the QPS and storage. Then design API, then data model, then high-level architecture. Never jump to solution without establishing the problem scope.
- **How long should each section take?** — Requirements: 5-10 min. API design: 5 min. Data model: 5-10 min. High-level design: 15-20 min. Optimizations/deep dive: 10-15 min. Total ~45-60 minutes. Keep requirements phase short — don't over-clarify, just cover scale, key features, and key constraints.
