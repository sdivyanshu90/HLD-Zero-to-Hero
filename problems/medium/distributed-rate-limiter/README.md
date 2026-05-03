# Distributed Rate Limiter — System Design Walkthrough

**Difficulty:** Medium  
**Tags:** token-bucket, sliding-window, Redis, Lua, distributed-systems  
**Companies:** Stripe, Cloudflare, AWS API Gateway, Kong

---

## Problem Statement

Design a distributed rate limiting service that:
- Enforces per-user, per-IP, and per-API-key request quotas
- Operates at 100 K req/sec cluster-wide with < 5 ms overhead per check
- Handles node failures without allowing uncontrolled traffic spikes
- Supports multiple algorithms (token bucket, sliding window)

---

## Architecture Diagram

```
Client Requests
       │
       ▼
┌──────────────────┐
│   API Gateway    │──── Rate Limit Middleware
└────────┬─────────┘          │
         │               ┌────▼──────────────────┐
         │               │   Redis Cluster        │
         │               │  (shared counters)     │
         │               │  Lua scripts (atomic)  │
         │               └────────────────────────┘
         ▼
  Upstream Service
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic Model and Capacity](02-traffic-model-and-capacity.md)
3. [API Surface and Limit Keys](03-api-surface-and-limit-keys.md)
4. [Token Bucket Algorithm](04-token-bucket-algorithm.md)
5. [Redis and Lua Atomicity](05-redis-and-lua-atomicity.md)
6. [High Availability and Failure Handling](06-high-availability-and-failure-handling.md)
7. [Clock Drift and Consistency](07-clock-drift-and-consistency.md)
8. [Checkpoint](08-checkpoint.md)
