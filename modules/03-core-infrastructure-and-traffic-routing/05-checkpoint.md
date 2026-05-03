# Module 03 Checkpoint: Core Infrastructure and Traffic Routing

## Questions to Test Your Understanding

---

**Q1.** You need to route /api/* requests to your API servers and /ws/* to your WebSocket servers, with SSL termination at the load balancer. Which type of load balancer do you need and why?

> **Answer:** Layer 7 (ALB, Nginx). An L4 LB cannot inspect URL paths — it only sees TCP/UDP. L7 terminates TLS, reads the HTTP request, and routes based on URL path. SSL termination at the LB means backends receive plain HTTP, simplifying cert management.

---

**Q2.** Your cache servers are arranged using consistent hashing. You remove one of 10 servers. Approximately what fraction of cache keys need to move?

> **Answer:** Approximately **1/10 (10%)** of keys need to be remapped — those previously assigned to the removed server. They move to the next server clockwise on the ring. In contrast, modular hashing (key % N) would change assignments for O(N) keys when N changes.

---

**Q3.** What is the "thundering herd" problem and how do you prevent it during CDN cache expiry?

> **Answer:** When a cached response expires simultaneously for all edge nodes, all of them send cache-miss requests to origin at the same moment, overwhelming it. Prevention strategies:
> - **Stale-while-revalidate**: serve stale immediately, revalidate in background
> - **Request coalescing**: CDN holds all concurrent cache-miss requests and only sends one origin pull
> - **TTL jitter**: vary TTL slightly so not all edges expire simultaneously

---

**Q4.** Why would you use a CDN for an API that returns dynamic, uncacheable responses?

> **Answer:** Even without caching, a CDN provides: (1) TCP connection termination near the user (reduces TCP handshake RTT), (2) routing over CDN private backbone instead of the public internet (lower, more consistent latency), (3) DDoS absorption at the edge, (4) TLS termination near the user. These benefits apply regardless of cacheability.

---

**Q5.** Design the traffic routing layer for a system that must route:
  - GET /api/v1/* → API service (standard requests)
  - POST /api/v1/upload → Upload service (large bodies, slow processing)
  - GET /admin/* → Admin service (requires admin JWT)
  - WebSocket /ws/* → WebSocket cluster

> **Answer:**
> - L4 NLB at the internet edge (handles raw TCP volume, DDoS absorption)
> - L7 ALB/Nginx behind it (terminates TLS, routes by path):
>   - `/api/v1/*` → API server pool (standard timeout 30s)
>   - `/api/v1/upload` → Upload server pool (long timeout 300s, separate pool to avoid HOL)
>   - `/admin/*` → API Gateway with JWT verification middleware → Admin service
>   - `/ws/*` → WebSocket pool (sticky sessions by cookie, long timeout/keep-alive)

---

## Checklist

- [ ] L4 LB: TCP/UDP only, no SSL termination, ultra-low overhead
- [ ] L7 LB: HTTP aware, SSL termination, URL/header routing
- [ ] Health checks: L4 (TCP SYN) vs L7 (HTTP 200)
- [ ] Round Robin → Least Connections → Consistent Hashing — when to use each
- [ ] Sticky sessions: useful for stateful apps, dangerous for availability
- [ ] Connection draining: prevent in-flight request drops during deployment
- [ ] Reverse Proxy: SSL, LB, caching, compression
- [ ] API Gateway: auth, rate limiting, routing, observability
- [ ] BFF pattern: per-client-type backend aggregation
- [ ] CDN: geographic caching, static assets, dynamic acceleration
- [ ] Cache-Control headers: max-age, s-maxage, stale-while-revalidate
- [ ] CDN invalidation: TTL expiry, purge API, versioned URLs, surrogate keys
