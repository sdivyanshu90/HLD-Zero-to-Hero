# Real-time Delivery: Polling, SSE, WebSockets, and WebRTC

## The Problem: Server Needs to Push to Client

HTTP is request-response: the client asks, the server answers. But many applications need the *server* to push data as events happen.

```
Examples requiring server push:
  Live sports score updates
  Stock ticker / order book
  Chat messages
  Collaborative document editing
  Live dashboard / monitoring
  Multiplayer game state
  Notification delivery
```

---

## Option 1: Short Polling

Client asks "any updates?" on a fixed timer:

```
Client                    Server
  │──── GET /updates ────▶│
  │◀─── 200 [] ───────────│  (empty, no updates)
  │     (wait 1 second)
  │──── GET /updates ────▶│
  │◀─── 200 [] ───────────│  (empty)
  │     (wait 1 second)
  │──── GET /updates ────▶│
  │◀─── 200 [{msg}] ──────│  (new message!)

Problems:
  - N clients × 1 req/sec = N requests/sec wasted on empty responses
  - 1 second lag even for urgent updates
  - Serverless/cloud cost: pay for every empty poll
```

### When Polling is Fine

```
Dashboard refreshing every 5 minutes? → Simple polling works.
Email client checking for new mail? → Polling every 30s is standard.
Social media feed? → Pull on scroll + push via long-poll for notifications.
```

---

## Option 2: Long Polling

Client holds a connection open until the server has something to say:

```
Client                    Server
  │──── GET /updates ────▶│
  │                        │  (server holds connection open)
  │                        │  (30 seconds pass...)
  │◀─── 200 [{msg}] ──────│  (finally has something!)
  │──── GET /updates ────▶│  (client immediately opens new request)

Or on timeout:
  │◀─── 204 No Content ───│  (30 second timeout, no data)
  │──── GET /updates ────▶│  (client re-opens)
```

**Trade-offs:**
- Lower bandwidth waste than short polling
- Still half-duplex (client initiates every "session")
- Each connection holds a server socket and thread (resource expensive at scale)
- Requires careful timeout/retry logic
- Used by: early push notification systems, some chat apps, Stripe webhooks retry

---

## Option 3: Server-Sent Events (SSE)

SSE is a simple HTTP/1.1 standard where the server streams events to a client over a persistent HTTP connection:

```
Client ──── GET /events ──────▶ Server
           (Accepts: text/event-stream)

Server keeps connection open and streams:
  data: {"event": "score", "value": "2-1"}\n\n
  data: {"event": "score", "value": "3-1"}\n\n
  event: goal\n
  data: {"scorer": "Messi", "minute": 78}\n\n
  : heartbeat (comment line, keeps connection alive)\n\n

Client auto-reconnects on disconnect (built into SSE spec)
```

### SSE Characteristics

```
✓ Simple HTTP — works through proxies, CDN, L7 LBs
✓ Auto-reconnect with Last-Event-ID (resume from where you left off)
✓ Native browser EventSource API (no library needed)
✓ Works over HTTP/2 (many parallel SSE streams on one connection)
✗ Server → client only (unidirectional)
✗ Text-only (UTF-8) by spec
✗ Max 6 connections per browser on HTTP/1.1 (not a problem on HTTP/2)
✗ No binary framing (overhead for binary data)

Use cases:
  Live feeds, news ticker, social media updates
  Dashboard monitoring, log streaming
  Notification delivery
```

---

## Option 4: WebSockets

WebSocket provides a full-duplex persistent connection. A single TCP connection supports both client→server and server→client messages simultaneously:

```
HTTP Upgrade Handshake:
  Client ──── GET /chat HTTP/1.1 ────▶ Server
              Upgrade: websocket
              Connection: Upgrade
              Sec-WebSocket-Key: ...

  Server ◀─── 101 Switching Protocols ─ Server
              Upgrade: websocket

  Now both sides can send frames at any time:

  Client ──── {"type":"message","text":"Hello"} ──▶ Server
  Client ◀─── {"type":"message","from":"Bob"} ────── Server
  Client ◀─── {"type":"typing","user":"Carol"} ────── Server
  Client ──── {"type":"seen","msgId":"123"} ──────▶ Server
```

### WebSocket Frame Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |                               |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
  2-byte minimum header → very low overhead vs HTTP headers (600+ bytes)
```

### WebSocket at Scale

```
1 million concurrent WebSocket connections:

  Each connection: ~50-100 KB RAM (file descriptor + buffers)
  1M connections: ~50-100 GB RAM on server!

  Problem: traditional thread-per-connection model fails
  Solution: async event loop (Node.js, Nginx, Netty, Go goroutines)

  With async I/O:
    Nginx: handles 100K+ connections on single server
    Node.js: 50K connections per server (with 100MB RAM baseline)

  Architecture:
    WebSocket servers behind sticky L7 LB
    → Sticky: client must reconnect to same server (session state in RAM)
    → OR: stateless WebSocket servers + Redis pub/sub for message routing
```

---

## Option 5: WebRTC

WebRTC enables peer-to-peer real-time media and data channels in browsers:

```
┌─────────────────────────────────────────────────────────────┐
│                  WebRTC Connection Setup                     │
│                                                              │
│  Browser A              Signaling Server        Browser B   │
│     │──── SDP Offer ────────────▶│                          │
│     │                            │──── SDP Offer ──────▶│  │
│     │◀─── SDP Answer ────────────│                        │ │
│     │◀─────────────────────────────── SDP Answer ────────│ │
│     │                                                      │ │
│     │──── ICE Candidate ─────────▶────────────────────▶│  │
│     │◀─────────────────────────────── ICE Candidate ────│ │
│     │                                                      │ │
│     │◄════════════════ P2P UDP Connection ════════════════▶│ │
│     │           (audio/video/data flows P2P)               │ │
└─────────────────────────────────────────────────────────────┘

If P2P fails (NAT/firewall): TURN relay server steps in
```

---

## Comparison: Which to Use When?

```
┌─────────────────────────────────────────────────────────────────┐
│              REAL-TIME DELIVERY DECISION MATRIX                  │
│                                                                   │
│  Feature         Polling  Long Poll  SSE   WebSocket  WebRTC    │
│  ───────────────────────────────────────────────────────────     │
│  Server→Client    ✓        ✓         ✓       ✓         ✓        │
│  Client→Server    ✓        ✓         ✗       ✓         ✓        │
│  Bidirectional    ✓(pair)  ✓(pair)   ✗       ✓         ✓        │
│  P2P              ✗        ✗         ✗       ✗         ✓        │
│  Low latency      ✗        Medium    Low     Low      Lowest    │
│  Simple setup     ✓        ✓         ✓       Medium    Complex  │
│  HTTP/proxy compat✓        ✓         ✓       Sometimes ✗        │
│  Binary support   ✓        ✓         ✗       ✓         ✓        │
│  Scalability      Easy     Medium    Easy    Hard      Medium   │
│  Auto-reconnect   App      App       Built-in App      App      │
└─────────────────────────────────────────────────────────────────┘
```

### Decision Guide

| Use Case | Recommendation | Why |
|----------|----------------|-----|
| Live feed / notifications | SSE | Unidirectional, simple, HTTP-compatible |
| Chat / collaboration | WebSocket | Bidirectional, low latency |
| Video call | WebRTC | P2P for lowest latency and server cost |
| Live dashboard | SSE or WebSocket | Depends on if client sends data |
| Game state (100ms updates) | WebSocket | Low overhead bidirectional |
| Infrequent updates | Long polling | Simpler than WebSocket for rare events |

---

## Interview Quick Answers

- **Why use WebSocket over SSE for chat?** — Chat is bidirectional (user types messages, server pushes messages from others). SSE is server-to-client only.
- **How do you scale WebSocket servers?** — Stateless servers + Redis pub/sub. When user A sends a message, broadcast it to Redis; all servers subscribed to the channel push to their connected clients.
- **What is SSE's advantage over WebSocket?** — Works over plain HTTP (no upgrade negotiation), easily cached/proxied, auto-reconnects, simpler server implementation.
- **When would you use WebRTC vs WebSocket for video?** — WebRTC for real-time A/V (P2P, low latency, handles jitter/loss). WebSocket for metadata/signaling alongside WebRTC, or for non-real-time video chat.
