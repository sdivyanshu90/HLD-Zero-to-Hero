# Reverse Proxies vs API Gateways

## What is a Reverse Proxy?

A reverse proxy sits in front of your servers and forwards client requests to them. From the client's perspective, it is talking to the proxy — it does not know the backend exists.

```
Forward proxy (client-side):
  Client ──▶ [Forward Proxy] ──▶ Internet
  Client uses proxy to access external resources
  Example: corporate network proxy, VPN

Reverse proxy (server-side):
  Internet ──▶ [Reverse Proxy] ──▶ Backend Servers
  Backend is hidden; proxy acts as face of the system
  Example: Nginx, HAProxy, Cloudflare
```

### What a Reverse Proxy Does

```
┌─────────────────────────────────────────────────────────────────┐
│                   REVERSE PROXY CAPABILITIES                     │
│                                                                   │
│  SSL/TLS Termination                                              │
│    Client ──HTTPS──▶ [Proxy] ──HTTP──▶ Backend                  │
│    → Backend doesn't need SSL certificates or overhead           │
│                                                                   │
│  Load Balancing                                                   │
│    → Distribute requests across backend pool (see Module 02)     │
│                                                                   │
│  Caching                                                          │
│    → Cache static assets, API responses                          │
│    → Serve cached responses without hitting backend              │
│                                                                   │
│  Compression                                                      │
│    → gzip/Brotli compress responses (saves bandwidth)            │
│                                                                   │
│  Request/Response Rewriting                                       │
│    → Rewrite URLs, add/remove headers                            │
│    → Strip sensitive headers before forwarding                   │
│                                                                   │
│  Connection Pooling                                               │
│    → Maintain warm connection pool to backends                   │
│    → Protect backends from connection storms                     │
│                                                                   │
│  Security                                                         │
│    → Hide backend topology from internet                         │
│    → Block malicious traffic, rate limit                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## What is an API Gateway?

An API Gateway is a specialized reverse proxy designed for microservices. It adds cross-cutting concerns that would otherwise be duplicated in every service:

```
┌────────────────────────────────────────────────────────────────┐
│                     API GATEWAY CAPABILITIES                    │
│                                                                  │
│  Authentication & Authorization                                  │
│    → Verify JWT/OAuth tokens before forwarding to any service   │
│    → Policy-based access control (can user X call service Y?)   │
│                                                                  │
│  Rate Limiting                                                   │
│    → Per-user, per-IP, per-API-key limits                       │
│    → Token bucket, sliding window algorithms                    │
│                                                                  │
│  Request Routing                                                 │
│    → /v1/users/* → user-service                                 │
│    → /v1/orders/* → order-service                               │
│    → Canary routing: 5% to v2, 95% to v1                        │
│                                                                  │
│  Protocol Translation                                            │
│    → External REST → Internal gRPC                              │
│    → External JSON → Internal Protobuf                          │
│                                                                  │
│  Observability                                                   │
│    → Log every request centrally                                 │
│    → Emit metrics (request rate, latency, errors per service)   │
│    → Distributed tracing (inject trace ID into forwarded req)   │
│                                                                  │
│  Circuit Breaking                                                │
│    → If user-service fails, stop sending requests to it         │
│    → Return fallback response immediately                        │
│                                                                  │
│  Caching                                                         │
│    → Cache responses at gateway level                           │
│    → Idempotent GET requests often cache-able                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Architecture Pattern: API Gateway + BFF

```
Single Gateway (monolithic):
  Mobile ──▶ Gateway ──▶ Multiple microservices
  Web    ──▶ Gateway ──▶ Multiple microservices
  Problem: one gateway must handle all client types (mobile needs less data)

Backend for Frontend (BFF) pattern:
  Mobile ──▶ Mobile BFF  ──▶ Microservices
  Web    ──▶ Web BFF     ──▶ Microservices
  IoT    ──▶ IoT BFF     ──▶ Microservices

  Each BFF is tailored to its client's needs:
    Mobile BFF: aggregates, compresses, minimizes payload
    Web BFF: full data, richer responses, browser-specific cookies
```

```
┌──────────────────────────────────────────────────────────────┐
│                   BFF ARCHITECTURE                            │
│                                                               │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │Mobile App │  │ Web App   │  │ IoT Device│               │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘               │
│        │               │               │                     │
│        ▼               ▼               ▼                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Mobile BFF│  │ Web BFF  │  │ IoT BFF  │                  │
│  └────┬─────┘  └─────┬────┘  └──────┬───┘                  │
│       └───────────────┼──────────────┘                      │
│                       ▼                                      │
│         ┌──────────────────────────┐                        │
│         │     Internal Services   │                         │
│         │  User  Order  Inventory │                         │
│         └──────────────────────────┘                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Reverse Proxy vs API Gateway Comparison

| Capability | Reverse Proxy (Nginx/HAProxy) | API Gateway (Kong/AWS Gateway) |
|------------|-------------------------------|--------------------------------|
| SSL termination | ✓ | ✓ |
| Load balancing | ✓ | ✓ |
| Request routing | Basic (path/host) | Advanced (JWT claims, headers) |
| Authentication | Basic (IP allow/deny) | Full JWT/OAuth/API key |
| Rate limiting | Basic (req/IP) | Per-user, per-plan, throttling |
| Protocol translation | No | REST↔gRPC, JSON↔Protobuf |
| Analytics/metrics | Basic (access log) | Full observability |
| Plugin ecosystem | Limited | Rich (Kong plugins) |
| Latency overhead | ~100µs | ~500µs–5ms |
| Configuration | Flat files | Dynamic API/UI |
| Examples | Nginx, HAProxy, Traefik | Kong, AWS API GW, Apigee, Envoy |

---

## Service Mesh vs API Gateway

An API Gateway handles **north-south** traffic (external→internal). A service mesh handles **east-west** traffic (service→service):

```
Internet ──▶ [API Gateway] ──▶ [Service A] ──▶ [Service B]
              North-South            East-West (service mesh)
              (Nginx/Kong)          (Istio/Envoy sidecar)

API Gateway:
  - One entry point for all external traffic
  - Auth, rate limiting, routing at the edge

Service Mesh (Istio, Linkerd):
  - Sidecar proxy (Envoy) runs beside every service
  - mTLS between all services (automatic)
  - Circuit breaking, retry, timeout between services
  - Distributed tracing automatically
  - No code changes required in services
```

---

## Interview Quick Answers

- **What is the difference between a reverse proxy and an API Gateway?** — A reverse proxy handles traffic forwarding (SSL, LB, caching). An API Gateway adds application-layer cross-cutting concerns (auth, rate limiting, routing, observability). In practice, many L7 reverse proxies can be configured as API gateways.
- **Why put an API Gateway in front of microservices?** — Avoid duplicating auth, rate limiting, logging in every service. Single enforcement point. Protocol translation (external REST to internal gRPC).
- **What is a BFF and when do you use it?** — Backend for Frontend: a specialized API gateway per client type (mobile, web, IoT). Reduces over-fetching, adapts response to each client's needs.
- **What is the overhead of an API Gateway?** — Typically 1-5ms added latency for auth check, rate limit check, logging. Can be reduced to ~0.5ms with local caching of auth decisions.
