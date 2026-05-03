# OSI Layer 4 and Layer 7

## The OSI Model Refresher

The OSI model has 7 layers. In system design, the relevant ones are Layer 4 (Transport) and Layer 7 (Application). Load balancers and proxies operate at one of these two layers, and the choice has major implications.

```
┌──────────────────────────────────────────────────────────────┐
│                     OSI MODEL (Simplified)                    │
│                                                               │
│  Layer 7  APPLICATION    HTTP, gRPC, WebSocket, DNS           │
│  ───────────────────────────────────────────────────────────  │
│  Layer 6  PRESENTATION   TLS/SSL, encoding (JSON, Protobuf)   │
│  ───────────────────────────────────────────────────────────  │
│  Layer 5  SESSION        TCP sessions, WebSocket sessions     │
│  ───────────────────────────────────────────────────────────  │
│  Layer 4  TRANSPORT      TCP, UDP — ports and reliability     │
│  ───────────────────────────────────────────────────────────  │
│  Layer 3  NETWORK        IP — routing between machines        │
│  ───────────────────────────────────────────────────────────  │
│  Layer 2  DATA LINK      Ethernet, MAC addresses, switches    │
│  ───────────────────────────────────────────────────────────  │
│  Layer 1  PHYSICAL       Cables, fiber, radio waves           │
└──────────────────────────────────────────────────────────────┘
```

---

## Layer 4: Transport Layer

Layer 4 deals with **ports, connections, and delivery guarantees**. It knows IP addresses and port numbers, but cannot read the content of packets.

### What L4 Can See

```
L4 packet view:
┌──────────────┬────────────┬──────────────────────────┐
│  Source IP   │  Dest IP   │  Source Port  Dest Port  │  TCP header
│  10.0.0.5    │  10.0.0.10 │    54321       80        │
├──────────────┴────────────┴──────────────────────────┤
│                  ENCRYPTED PAYLOAD                     │  L4 cannot read this
└────────────────────────────────────────────────────────┘
```

### L4 Load Balancing

An L4 load balancer routes based on IP and port only. It does not decrypt TLS, does not read HTTP headers, does not know URL paths.

```
L4 Load Balancer (AWS NLB, HAProxy TCP mode):

Client ──▶ LB (IP: 203.0.113.1:443)
           │
           ├──▶ Server A (10.0.0.1:443)  ← based on connection hash
           ├──▶ Server B (10.0.0.2:443)
           └──▶ Server C (10.0.0.3:443)

LB sees: source IP, dest IP, ports — nothing else
LB can do: round-robin TCP connections, least-connections, IP-hash sticky
LB cannot do: route /api to one backend and /static to another
```

**Advantages:**
- Extremely fast (no TLS termination, no HTTP parsing)
- Can handle any TCP/UDP protocol, not just HTTP
- Single-digit microsecond overhead

**Disadvantages:**
- No application-level routing (cannot route by URL, header, cookie)
- No SSL termination (backend servers each need TLS certificates)
- Sticky sessions must be IP-based (problematic behind NAT)

---

## Layer 7: Application Layer

Layer 7 operates on the *content* of requests. It can read HTTP headers, URL paths, cookies, JWT tokens, and the request body.

### What L7 Can See

```
L7 request view:
┌──────────────────────────────────────────────────────────────────┐
│  HTTP/2 Request:                                                  │
│  GET /api/v2/users/1234                                          │
│  Host: api.example.com                                           │
│  Authorization: Bearer eyJhbGci...                               │
│  X-User-Region: eu-west                                          │
│  Cookie: session=abc123                                          │
│  Content-Type: application/json                                  │
└──────────────────────────────────────────────────────────────────┘
  ↑ L7 load balancer / API gateway can read and act on all of this
```

### L7 Load Balancing

```
L7 Load Balancer (Nginx, AWS ALB, Envoy):

Client ──▶ LB (terminates TLS, reads HTTP)
           │
           ├──▶ API servers  (routes: /api/*)
           ├──▶ Auth servers (routes: /auth/*)
           ├──▶ Static CDN   (routes: /static/*)
           └──▶ WebSocket    (routes: /ws/*, upgrades connection)

Routing decisions can be based on:
  - URL path prefix or regex
  - HTTP headers (Host, Authorization, X-Custom)
  - Cookies
  - Query parameters
  - Request method (GET vs POST)
  - JWT claims (after token verification)
```

---

## Layer 4 vs Layer 7 Comparison

```
Feature                    L4 (TCP/UDP)         L7 (HTTP)
──────────────────────────────────────────────────────────
TLS termination            No                   Yes
URL-based routing          No                   Yes
Header inspection          No                   Yes
Authentication/JWT check   No                   Yes
HTTP/2 multiplexing        No (TCP only)         Yes
WebSocket support          Yes (pass-through)    Yes (upgrade)
Protocol agnostic          Yes (any TCP/UDP)     HTTP/gRPC only
Overhead                   ~10 µs               ~100 µs
Connection reuse           No                   Yes (pooling)
Health checks              TCP handshake        HTTP 200 check
Use case                   High volume, any protocol  Web, API routing
```

---

## TCP Connection Lifecycle (L4 Internals)

```
TCP 3-Way Handshake (must complete before first byte of data):

Client          Server
  │──── SYN ────▶│     "I want to connect"
  │◀─── SYN-ACK ─│     "OK, I'm listening"
  │──── ACK ────▶│     "Connection established"
  │              │
  │  DATA ──────▶│     (first real request)
  │◀──────── DATA│     (response)
  │              │
  │──── FIN ────▶│     "Closing connection"
  │◀─── FIN-ACK ─│
  │──── ACK ────▶│

Cost: 1.5 × RTT before first byte (at 500µs DC RTT: 750µs overhead)
TLS adds another 1 RTT (TLS 1.2) or 0.5 RTT (TLS 1.3) on top
```

### Connection Pooling

```
Without pooling (new TCP+TLS per request):
  Each request: 1.5 RTT (TCP) + 1 RTT (TLS) + 0.5 RTT (HTTP) = 3 RTT
  At 500µs RTT: 1.5ms overhead per request!

With connection pooling:
  First request: 3 RTT setup
  Subsequent: 0.5 RTT (just the HTTP request/response)
  → 6× lower latency for established connections
```

---

## Real-World Architecture Patterns

```
Typical 3-tier setup:

Internet
   │
   ▼
L4 LB (AWS NLB)          ← handles millions of TLS connections cheaply
   │                         routes TCP by IP hash
   ▼
L7 LB (AWS ALB / Nginx)  ← terminates TLS, inspects HTTP
   │                         routes by path/header/cookie
   ├──▶ /api/*  → App Servers (fleet)
   ├──▶ /auth/* → Auth Service
   ├──▶ /ws/*   → WebSocket Servers
   └──▶ /static/* → S3 / CDN origin
```

---

## Interview Quick Answers

- **Which layer does an API Gateway operate at?** — L7. It reads HTTP headers, routes requests, applies auth middleware, rate limits.
- **Why is NLB faster than ALB?** — NLB operates at L4 (no HTTP parsing, no TLS termination at LB). ALB parses HTTP, which adds ~100µs.
- **What's the downside of L4 load balancing?** — Cannot do intelligent routing; all requests to the same backend once connection is established (connection is sticky).
- **How does WebSocket work at L7?** — Client sends HTTP Upgrade header; L7 proxy completes the upgrade and then proxies the raw TCP stream, effectively becoming a TCP passthrough for the duration of the session.
