# URL Shortener — System Design Walkthrough

**Difficulty:** Easy  
**Tags:** hashing, caching, RDBMS, key-generation  
**Companies:** Twitter, Bitly, Google (goo.gl)

---

## Problem Statement

Design a highly available URL shortening service (like TinyURL / Bit.ly) that:
- Accepts a long URL and returns a unique 7-character short code
- Redirects any valid short code to the original URL with < 10 ms p99 latency
- Stores up to 5 years of data
- Handles 100 M new URLs/month write rate and 10× that on reads

---

## Table of Contents

1. [Requirements](01-requirements.md)
2. [Back-of-the-Envelope Estimation](02-back-of-the-envelope-estimation.md)
3. [API Design](03-api-design.md)
4. [Data Model and Storage](04-data-model-and-storage.md)
5. [High-Level Architecture](05-high-level-design.md)
6. [Key Generation](06-key-generation.md)
7. [Redirect Caching](07-redirect-caching.md)
8. [Checkpoint](08-checkpoint.md)

---

## High-Level Architecture Diagram

```
Client
  │
  ▼
┌──────────────────────────────┐
│         API Gateway          │  rate-limit  •  TLS termination
└──────────┬───────────────────┘
           │
     ┌─────┴──────┐
     │            │
  Write        Read / Redirect
     │            │
     ▼            ▼
┌─────────┐   ┌────────────────────────┐
│  API    │   │   Redirect Service     │
│ Service │   │ (stateless, many pods) │
└────┬────┘   └──────────┬─────────────┘
     │                   │
     │           ┌───────┴────────┐
     │           │   Redis Cache  │  TTL 24h, ~100 GB
     │           └───────┬────────┘
     │                   │ cache miss
     ▼                   ▼
┌────────────────────────────────┐
│  MySQL / PostgreSQL (Primary)  │  short_codes table
│  ── Replica(s) for reads ──    │
└────────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│  Key Generation Svc  │  pre-generated codes (KGS)
│  (optional offline   │
│   batch approach)    │
└──────────────────────┘
```

---

## Decision Checklist (Interview Quick Reference)

| Question | Answer |
|----------|--------|
| Code length? | 7 chars base62 = 62^7 ≈ 3.5 T unique codes |
| Code generation? | Random + bloom-filter collision check OR pre-generated table |
| Cache hit rate? | ~80 % of reads hit Redis (Pareto principle) |
| Redirect type? | 301 (browser-cached, saves traffic) vs 302 (server sees every hit) |
| Primary store? | Relational DB; schema is simple key-value-like |
| Availability? | Read replicas + Redis; writes can lag behind |
| Expiry cleanup? | TTL column + nightly batch delete job |
