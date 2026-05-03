# Load Balancers

## What is a Load Balancer?

A load balancer distributes incoming requests across a pool of backend servers. The goal is to maximize availability, throughput, and resource utilization while preventing any single server from becoming a bottleneck.

```
┌────────────────────────────────────────────────────────────────────┐
│                       LOAD BALANCER ROLE                            │
│                                                                      │
│  Clients                 Load Balancer            Servers           │
│  ┌──────┐                ┌───────────┐            ┌──────┐         │
│  │Client│──── req ──────▶│           │──── req ──▶│  A   │ 40 req  │
│  └──────┘                │    LB     │            └──────┘         │
│  ┌──────┐                │           │──── req ──▶┌──────┐         │
│  │Client│──── req ──────▶│  (single  │            │  B   │ 35 req  │
│  └──────┘                │  IP/DNS)  │──── req ──▶└──────┘         │
│  ┌──────┐                │           │            ┌──────┐         │
│  │Client│──── req ──────▶│           │──── req ──▶│  C   │ 25 req  │
│  └──────┘                └───────────┘            └──────┘         │
│                                                                      │
│  Clients see one address.  LB distributes evenly.                   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Layer 4 vs Layer 7 Load Balancers

### L4 Load Balancer (Transport Layer)

Operates on IP address and TCP/UDP port. Does not inspect packet content:

```
L4 decision: {src IP, src port, dst IP, dst port} → pick backend

AWS Network Load Balancer (NLB):
  - Ultra-low latency (~microseconds overhead)
  - Handles any TCP/UDP protocol
  - Cannot route based on URL, headers, or body
  - Cannot do SSL termination (passes TLS through)
  - Used for: raw TCP services, UDP services, high-volume TCP where HTTP parsing is unnecessary
```

### L7 Load Balancer (Application Layer)

Fully parses HTTP requests. Can route based on any request attribute:

```
L7 decision: {HTTP method, URL path, Host header, cookie, JWT, query param} → pick backend

AWS Application Load Balancer (ALB) / Nginx / Envoy:
  - Can route /api/* to API servers, /static/* to file servers
  - SSL termination (one cert on LB, not on every backend)
  - Health checks via HTTP endpoint (GET /health → 200 OK)
  - Cookie-based sticky sessions
  - Request/response rewriting
  - Rate limiting (on some implementations)
  - ~100µs overhead (parsing HTTP adds cost vs L4)
```

---

## Health Checks

A load balancer continuously probes backends. Unhealthy backends are removed from the pool:

```
L4 Health Check:
  LB ──── TCP SYN ──────▶ Backend
  LB ◀─── TCP SYN-ACK ─── Backend  → HEALTHY
  If SYN-ACK not received within 5s → UNHEALTHY → remove from pool

L7 Health Check:
  LB ──── GET /health HTTP/1.1 ──▶ Backend
  LB ◀─── 200 OK {"status":"ok"} ── Backend  → HEALTHY
  If 5xx or timeout → UNHEALTHY

Health check config:
  Interval:          5 seconds
  Timeout:           3 seconds
  Healthy threshold: 2 consecutive successes
  Unhealthy threshold: 3 consecutive failures

Failure detection time: 3 failures × 5s = 15 seconds of unavailability
→ Design health checks to be fast and reliable
```

---

## Sticky Sessions (Session Affinity)

Some applications store session state on the server (in-memory). Sticky sessions ensure a client always routes to the same backend:

```
Without sticky sessions (stateful app):
  Client ──── request 1 ──▶ Server A (stores session)
  Client ──── request 2 ──▶ Server B (no session!) → 401 Unauthorized!

With sticky sessions (cookie-based):
  First request: LB assigns client to Server A, sets cookie AWSALB=hash-A
  All subsequent: client sends AWSALB cookie → LB routes to Server A

Problems:
  - Server A failure → all its sticky sessions lost
  - Uneven load if some clients generate much more traffic
  - Makes deployments harder (cannot drain Server A without losing sessions)

Better solution: store session in shared Redis
  → Stateless backends, no sticky needed, any server handles any request
```

---

## Connection Draining (Deregistration Delay)

When removing a backend from the pool (deployment, scale-in), in-flight requests must complete:

```
Naive removal:
  LB ──── stop routing to Server A
  Server A ──── killed immediately
  In-flight requests → Connection Reset → 500 errors to users!

With connection draining:
  1. LB marks Server A as "draining" (no new connections routed)
  2. LB waits for in-flight requests to complete (up to 300 seconds)
  3. Server A gracefully finishes all requests
  4. LB removes Server A entirely

AWS ALB deregistration delay: default 300 seconds (tunable to 0-3600)
For fast deploys (short requests): set to 30 seconds
For long requests (batch jobs): set to 600 seconds
```

---

## Types of Load Balancers in Practice

```
DNS Load Balancing:
  api.example.com → [10.0.0.1, 10.0.0.2, 10.0.0.3]
  DNS round-robin rotates which IP is returned
  ✓ No single LB needed
  ✗ DNS TTL caching means traffic doesn't shift immediately
  ✗ No health checking (bad IPs stay in rotation until TTL expires)
  Used for: geographic routing (Route 53), CDN edge selection

Hardware LB (F5, A10):
  Physical appliance, handles millions of connections
  Used by: financial institutions, telco, legacy enterprise
  ✓ Very high throughput, hardware offloading
  ✗ Expensive, not programmable, single point of failure

Software LB (Nginx, HAProxy, Envoy):
  Runs on commodity hardware
  ✓ Cheap, flexible, configurable
  Used by: most modern cloud deployments

Cloud LB (AWS ALB/NLB, GCP LB, Azure LB):
  Managed service, auto-scales, built-in DDoS protection
  ✓ No operational burden
  ✗ Vendor lock-in, limited customization
```

---

## Active-Active vs Active-Passive HA for Load Balancers

```
Active-Passive (failover):
  LB-1 (Active)  ←── receives all traffic
  LB-2 (Standby) ←── on standby, takes over if LB-1 fails

  VRRP/heartbeat protocol: LB-1 broadcasts "I'm alive" to LB-2
  If LB-2 stops receiving → promotes itself → takes virtual IP

  Failover time: ~5-30 seconds (DNS propagation or ARP takeover)

Active-Active (both serve traffic):
  LB-1 ←── handles 50% of traffic (Anycast routing)
  LB-2 ←── handles 50% of traffic
  If one fails: the other handles 100% (if capacity allows)

  Better utilization, instant failover, but requires stateless LBs
  Cloud providers use active-active behind a single DNS name
```

---

## Interview Quick Answers

- **Why use a load balancer if you have only 2 servers?** — High availability. Without an LB, losing one server means 50% of requests fail. With an LB, it detects the failure and routes 100% to the surviving server.
- **What is an NLB vs ALB?** — NLB = Layer 4 (TCP/UDP, ultra-low latency, no HTTP awareness). ALB = Layer 7 (HTTP routing, SSL termination, header-based routing).
- **How does a load balancer avoid being a single point of failure?** — Run 2+ LBs in active-active with Anycast IP or DNS round-robin. Cloud LBs are managed services that are inherently highly available.
- **What is the danger of sticky sessions?** — Server failure loses all sticky sessions assigned to it. Prefer shared session storage (Redis) so any server can handle any request.
