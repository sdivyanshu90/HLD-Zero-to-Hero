# Module 10: Microservices, Resilience and Security

## Overview

Microservices unlock team autonomy and independent scaling, but introduce distributed systems complexity. This module covers the patterns that make microservices reliable in production.

---

## What You Will Learn

```
┌──────────────────────────────────────────────────────────────┐
│              MODULE 10 LEARNING MAP                           │
│                                                                │
│  01-microservices-trade-offs                                  │
│     └── Monolith vs microservices, DDD boundaries, API GW    │
│                    │                                          │
│                    ▼                                          │
│  02-rate-limiting-algorithms                                  │
│     └── Token bucket, leaky bucket, sliding window           │
│         Distributed rate limiting with Redis                  │
│                    │                                          │
│                    ▼                                          │
│  03-circuit-breakers-and-bulkheads                           │
│     └── Circuit breaker states, bulkhead isolation           │
│         Timeouts, retries, fallbacks                          │
│                    │                                          │
│                    ▼                                          │
│  04-service-mesh-and-discovery                               │
│     └── Service registry, client vs server-side discovery    │
│         Service mesh (Istio/Envoy), health checks            │
│                    │                                          │
│                    ▼                                          │
│  05-authentication-and-security                              │
│     └── JWT (RS256), OAuth2/OIDC, mTLS, security checklist  │
└──────────────────────────────────────────────────────────────┘
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-microservices-trade-offs.md](01-microservices-trade-offs.md) | Monolith vs microservices, API gateway |
| [02-rate-limiting-algorithms.md](02-rate-limiting-algorithms.md) | Token bucket, sliding window |
| [03-circuit-breakers-and-bulkheads.md](03-circuit-breakers-and-bulkheads.md) | Resilience patterns |
| [04-service-mesh-and-discovery.md](04-service-mesh-and-discovery.md) | Discovery, Istio, mTLS |
| [05-authentication-and-security.md](05-authentication-and-security.md) | JWT, OAuth2, security checklist |
| [06-checkpoint.md](06-checkpoint.md) | Self-test questions |
