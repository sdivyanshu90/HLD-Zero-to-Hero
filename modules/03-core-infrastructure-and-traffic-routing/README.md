# Module 03: Core Infrastructure and Traffic Routing

## Overview

Before a request reaches your application code, it travels through several layers of infrastructure: DNS, load balancers, proxies, and possibly a CDN. Understanding these layers tells you where to apply rate limiting, caching, auth enforcement, and traffic shaping.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│           MODULE 03 LEARNING MAP                                │
│                                                                  │
│  01-load-balancers                                              │
│     └── L4 vs L7, health checks, sticky sessions               │
│         Connection draining, active-active HA                  │
│                    │                                            │
│                    ▼                                            │
│  02-routing-algorithms                                          │
│     └── Round Robin, Least Connections, Consistent Hashing     │
│         Power of Two Choices, Weighted routing                 │
│                    │                                            │
│                    ▼                                            │
│  03-reverse-proxies-vs-api-gateways                            │
│     └── Reverse proxy: SSL, LB, caching, compression          │
│         API Gateway: auth, rate limit, routing, observability  │
│         BFF pattern, Service Mesh                              │
│                    │                                            │
│                    ▼                                            │
│  04-cdns                                                        │
│     └── Cache tiers, Cache-Control headers, hit ratio          │
│         Invalidation strategies, security features            │
└────────────────────────────────────────────────────────────────┘
```

---

## Typical Production Traffic Flow

```
User Request Journey:

DNS Resolution
    │ (returns CDN/LB IP)
    ▼
CDN Edge PoP
    │ (cache hit → serve, cache miss → forward)
    ▼
L4 Load Balancer (AWS NLB)
    │ (TCP-level distribution, DDoS absorption)
    ▼
L7 Load Balancer / API Gateway (AWS ALB / Nginx)
    │ (SSL termination, URL routing, auth check, rate limit)
    ▼
Application Server
    │
    ▼
Database / Cache / Message Queue
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-load-balancers.md](01-load-balancers.md) | LB types, health checks, sticky sessions, HA |
| [02-routing-algorithms.md](02-routing-algorithms.md) | Round Robin, Consistent Hashing, Power-of-Two |
| [03-reverse-proxies-vs-api-gateways.md](03-reverse-proxies-vs-api-gateways.md) | Proxy vs Gateway, BFF, service mesh |
| [04-cdns.md](04-cdns.md) | CDN architecture, cache headers, invalidation |
| [05-checkpoint.md](05-checkpoint.md) | Self-test questions |
