# HTTP Evolution: HTTP/1.1, HTTP/2, HTTP/3

## HTTP/1.0: One Request Per Connection

Every HTTP/1.0 request required a new TCP connection (3-way handshake + TLS handshake):

```
Client                    Server
  │──── TCP SYN ─────────▶│
  │◀─── TCP SYN-ACK ───────│   1.5 RTT setup
  │──── TCP ACK ─────────▶│
  │──── TLS Hello ────────▶│
  │◀─── TLS Response ──────│   1 RTT TLS (TLS 1.3)
  │──── GET /page.html ───▶│
  │◀─── 200 OK + HTML ─────│   1 RTT request
  │
  │──── NEW TCP+TLS ───────▶│   3 RTT per resource!
  │──── GET /style.css ───▶│
  ...

A page with 50 resources = 50 × 3 RTT = 150 RTTs
At 50ms RTT: 7.5 seconds just for setup overhead!
```

---

## HTTP/1.1: Keep-Alive and Pipelining

HTTP/1.1 added persistent connections (keep-alive) and pipelining:

```
HTTP/1.1 Keep-Alive:
  One TCP connection, multiple requests:

  ──── GET /page.html ─────▶
  ◀─── 200 OK + HTML ────────
  ──── GET /style.css ─────▶   (same connection!)
  ◀─── 200 OK + CSS ─────────
  ──── GET /image.png ─────▶
  ◀─── 200 OK + PNG ─────────

  Still sequential: must wait for each response before next request

HTTP/1.1 Pipelining (rarely used in practice):
  ──── GET /page.html ─────▶
  ──── GET /style.css ─────▶   (sent without waiting)
  ──── GET /image.png ─────▶
  ◀─── 200 + HTML ───────────
  ◀─── 200 + CSS ────────────
  ◀─── 200 + PNG ────────────
  Still ordered! If HTML is slow, CSS and PNG must wait → HOL blocking
```

**Workaround**: browsers open **6 parallel TCP connections** per host, effectively multiplying throughput 6×. But each connection has its own TCP slow start, TLS overhead.

---

## HTTP/2: Multiplexing on One Connection

HTTP/2 introduces **streams** — logical channels on a single TCP connection:

```
┌───────────────────────────────────────────────────────────────┐
│                    HTTP/2 MULTIPLEXING                         │
│                                                                │
│  Single TCP Connection                                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Stream 1: GET /page.html  ─────────────────▶ HEADERS  │  │
│  │                            ◀─────────────── DATA DATA  │  │
│  │  Stream 2: GET /style.css  ───────────────▶ HEADERS    │  │
│  │                            ◀──────────── DATA          │  │
│  │  Stream 3: GET /api/user   ─────────────────▶ HEADERS  │  │
│  │                            ◀─────────────── DATA       │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  All 3 streams interleaved on ONE TCP connection               │
│  No head-of-line blocking at HTTP level                        │
│  (TCP-level HOL blocking remains if packets are lost)          │
└───────────────────────────────────────────────────────────────┘
```

### HTTP/2 Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| Binary framing | Frames replace text headers | Efficient parsing, no ambiguity |
| Header compression (HPACK) | Compress and deduplicate headers | Headers often ~800 bytes → ~50 bytes |
| Stream prioritization | Client hints which streams matter more | Critical CSS loads before images |
| Server push | Server sends resources proactively | Client doesn't need to ask for sub-resources |
| Flow control | Per-stream and connection-level | Backpressure without blocking other streams |

### Header Compression Example

```
HTTP/1.1 (repeated headers on every request):
  GET /api/user
  Host: api.example.com          ← 20 bytes
  Authorization: Bearer eyJ...    ← 500+ bytes  (JWT token!)
  Accept: application/json        ← 25 bytes
  User-Agent: Mozilla/5.0...      ← 60 bytes
  → ~600 bytes header overhead per request

HTTP/2 HPACK:
  First request: full headers sent, cached in HPACK table
  Subsequent:    refer to cached header by index
  → 2-20 bytes for same headers → 30× compression
```

---

## HTTP/3: QUIC-Based, No TCP

HTTP/3 replaces TCP with QUIC, solving TCP's HOL blocking completely:

```
┌──────────────────────────────────────────────────────────┐
│           PROTOCOL STACK COMPARISON                       │
│                                                           │
│  HTTP/1.1       HTTP/2          HTTP/3                    │
│  ─────────      ─────────       ─────────                 │
│  HTTP/1.1       HTTP/2          HTTP/3                    │
│  TLS 1.2        TLS 1.3         TLS 1.3 (in QUIC)         │
│  TCP             TCP             QUIC (UDP-based)          │
│  IP              IP              IP                        │
│                                                           │
│  Connections:  Multiple or 1   1                1         │
│  HOL blocking: HTTP level      Eliminated  Eliminated     │
│  TCP HOL:      Yes             Yes         No (per-stream)│
│  Setup RTT:    2.5             2.5         1 (0-RTT)      │
│  IP migration: No              No          Yes (QUIC CID) │
└──────────────────────────────────────────────────────────┘
```

### 0-RTT Connection Resumption

```
First connection (client new to server):
  Client ──── ClientHello ──────▶ Server
  Client ◀─── ServerHello + Key ─ Server
  Client ──── [first data] ──────▶          ← 1 RTT before data

Subsequent connections (session ticket remembered):
  Client ──── 0-RTT data + SessionTicket ──▶ Server  ← 0 RTT!
  Server can start processing immediately

Security trade-off: 0-RTT data is replay-attackable
→ Only safe for idempotent requests (GET, but not POST payment)
```

---

## HTTP Version Comparison Summary

| Feature | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---------|----------|--------|--------|
| Connections per host | 6 parallel | 1 | 1 |
| Multiplexing | No | Yes (streams) | Yes (streams) |
| Header compression | No | HPACK | QPACK |
| Server push | No | Yes | Yes |
| Transport | TCP | TCP | QUIC (UDP) |
| TCP HOL blocking | Yes | Yes | No |
| 0-RTT resumption | No | No | Yes |
| Connection migration | No | No | Yes |
| Adoption (2024) | ~15% | ~65% | ~30%+ |

---

## When Each Version Matters

```
HTTP/1.1: Legacy systems, simple internal APIs, IoT devices with constrained clients

HTTP/2: Default for all modern web APIs, gRPC (requires HTTP/2), HTTPS APIs

HTTP/3: Mobile apps (frequent WiFi→LTE switches benefit from connection migration)
        High-packet-loss environments (cellular, satellite)
        Large CDNs (Cloudflare, AWS CloudFront serve HTTP/3)
        Real-time APIs needing low latency at scale
```

---

## Interview Quick Answers

- **Why does gRPC require HTTP/2?** — gRPC uses bidirectional streaming which requires HTTP/2 multiplexed streams. HTTP/1.1 cannot support simultaneous request and response streams.
- **What is HTTP/2 server push and when is it useful?** — Server proactively sends resources the client will likely need. Useful for: push CSS/JS alongside HTML. Largely superseded by preload hints and service workers.
- **Why does HTTP/3 use UDP instead of TCP?** — TCP's head-of-line blocking affects all streams when one packet is lost. QUIC (on UDP) implements per-stream reliability, so a lost packet in stream 1 doesn't block stream 2.
