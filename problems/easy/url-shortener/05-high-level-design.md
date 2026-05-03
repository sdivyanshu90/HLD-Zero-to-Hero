# Step 5 — High-Level Architecture

## Component Diagram

```
                        ┌──────────────┐
                        │  DNS / CDN   │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │ API Gateway  │ TLS, rate-limit, auth
                        └──┬───────┬───┘
                           │       │
               ┌───────────┘       └───────────┐
               ▼                               ▼
     ┌──────────────────┐          ┌──────────────────────┐
     │   Write Service  │          │   Redirect Service   │
     │  (creates codes) │          │  (stateless, N pods) │
     └────────┬─────────┘          └──────────┬───────────┘
              │                               │
              │                    ┌──────────▼──────────┐
              │                    │     Redis Cluster    │
              │                    │  (hot URL mappings)  │
              │                    └──────────┬───────────┘
              │                               │ miss
              ▼                               ▼
     ┌────────────────────────────────────────────────┐
     │            MySQL Primary (writes)              │
     │            MySQL Replica × N  (reads)          │
     └────────────────────────────────────────────────┘
              │
              ▼
     ┌─────────────────┐
     │   Key Gen Svc   │  pre-fills "available_codes" pool
     └─────────────────┘
```

## Write Path (detailed)

```
1. Client → API Gateway (rate limit check)
2. API Gateway → Write Service
3. Write Service validates URL (regex + DNS lookup optional)
4. Write Service → Key Gen Svc: request 1 code
5. Key Gen Svc returns code (from pre-generated pool or random+check)
6. Write Service INSERTs into MySQL Primary
7. Write Service optionally SETs in Redis (TTL 24h)
8. Returns 201 with short URL
```

## Read / Redirect Path (critical path)

```
1. Client → API Gateway → Redirect Service
2. Redirect Service: Redis GET short_code
   ├── HIT  → return 301 Location header  (< 5 ms)
   └── MISS → MySQL Replica SELECT WHERE short_code = ?
               ├── found  → Redis SET (TTL 24h) + return 301
               └── not found → return 404 or 410 (if expired)
```

## Failure Modes

| Failure | Mitigation |
|---------|------------|
| Redis down | Fall through to MySQL; add circuit breaker |
| MySQL primary down | Reads still work via replica; writes queue in Kafka |
| Key Gen Svc down | Fall back to random code generation inline |
| Write service crash mid-insert | DB unique constraint prevents duplicate; retry is safe |

## Scalability Levers

```
Redirect Service: stateless → add pods via HPA (k8s)
Redis: shard by first 2 chars of short_code (Cluster mode)
MySQL: promote replica → primary; add read replicas
Key Gen Svc: stateless pool with 1 M pre-allocated codes
```
