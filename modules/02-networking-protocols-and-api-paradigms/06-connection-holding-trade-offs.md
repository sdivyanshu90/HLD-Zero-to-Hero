# Connection-Holding Trade-offs

## The Fundamental Problem

Persistent connections (WebSocket, SSE, long-polling, gRPC streaming) allow low-latency server push but they consume server resources for the entire duration of the connection — even when idle.

```
Short-lived connection (REST):
  Client                Server
    │── request ──────▶ │  socket open
    │◀─ response ─────── │  socket closed
    │                    │  0 resources consumed when idle

Long-lived connection (WebSocket):
    │═══════════════════│  socket OPEN for hours
    │  (idle 99% of time)│  still consuming:
    │                    │  - file descriptor
    │                    │  - receive/send buffers (~64KB each)
    │                    │  - state in load balancer
    │                    │  - RAM for connection state in app server
```

---

## Resource Cost Per Connection

```
Per WebSocket connection on a typical server:
  OS file descriptor:     ~8 bytes (descriptor table entry)
  TCP socket buffers:     ~128 KB (64KB send + 64KB receive, tunable)
  Application state:      ~2-10 KB (session data, channel membership)
  Load balancer entry:    ~1 KB

Realistic RAM per connection: 150-200 KB

1,000 concurrent connections:   ~200 MB RAM
100,000 concurrent connections: ~20 GB RAM
1,000,000 connections:          ~200 GB RAM  ← needs cluster!
```

---

## Heartbeats and Keep-Alive

Idle connections can be killed by:
- NAT devices timing out (typically 30s-5min)
- Load balancers timing out idle connections
- Intermediate proxies closing stale connections

Heartbeats prevent this and detect dead connections:

```
WebSocket Ping/Pong:
  Server ──── PING frame ──▶ Client   (every 30 seconds)
  Server ◀─── PONG frame ─── Client

  If PONG not received within N seconds → connection dead → clean up resources

TCP Keep-Alive (OS level):
  After 2 hours idle (default), OS sends TCP ACK probe
  → Way too slow for detecting dead clients!
  → Always use application-level heartbeats (30-60 seconds)
```

---

## Load Balancing with Persistent Connections

Long-lived connections create a **load imbalance** problem:

```
Initial state (balanced):
  LB routes new connections round-robin
  Server A: 1,000 connections  (all opened at 9am)
  Server B: 1,000 connections  (all opened at 9am)
  Server C: 1,000 connections  (all opened at 9am)

After 2 hours (no reconnects):
  Server A: 800 connections  (some clients disconnected)
  Server B: 900 connections
  Server C: 600 connections  ← underloaded

New connections route to C but old ones stay → permanent imbalance

Solution: periodic client reconnection jitter
  Client: reconnect every 4-8 hours + random jitter (±30 min)
  → Gradually redistributes connections
```

---

## Horizontal Scaling of WebSocket Servers

The critical challenge: WebSocket connections are **stateful** (tied to a specific server). When a user A (on Server 1) sends to user B (on Server 2), how does the message get there?

```
Without routing layer (broken):
  Server 1 (User A) ──✗──▶ Server 2 (User B)  ← no connection between servers!

With Pub/Sub bus:
  Server 1  ──── publish("room:123", msg) ──▶  Redis Pub/Sub
  Server 2  ◀─── subscribe("room:123") ───────  Redis Pub/Sub
  Server 2 delivers to User B

Architecture:
  User A (on WS Server 1) sends message
  WS Server 1 publishes to Redis channel "room:123"
  All WS Servers subscribed to "room:123" receive it
  Only WS Server 2 has User B connected → delivers to B

This pattern: used by Socket.io Redis adapter, Discord, Slack
```

```
┌────────────────────────────────────────────────────────────┐
│              WEBSOCKET CLUSTER ARCHITECTURE                 │
│                                                             │
│  Client A ──── WS ──▶ [WS Server 1] ──▶ Redis Pub/Sub     │
│  Client B ──── WS ──▶ [WS Server 2] ──▶ Redis Pub/Sub     │
│  Client C ──── WS ──▶ [WS Server 3] ──▶ Redis Pub/Sub     │
│                               ↑                            │
│               All servers subscribe to relevant channels   │
│               Deliver to locally-connected clients         │
└────────────────────────────────────────────────────────────┘
```

---

## Graceful Connection Draining

When deploying a new version of a WebSocket server, you cannot just restart it — you'd drop all connections:

```
Naive deploy:
  Kill server → all 10,000 connections drop → all clients reconnect
  → Thundering herd: DB and auth service get 10,000 reconnects in 1 second!

Graceful drain:
  1. Mark server as "draining" (stop accepting new connections)
  2. LB routes new connections to other servers
  3. Send close frame to existing connections with reconnect hint
  4. Clients reconnect with exponential backoff + jitter
  5. After 60 seconds, all connections migrated, kill old server

Exponential backoff with jitter:
  Client reconnects:
    attempt 1: wait random(0, 1)s
    attempt 2: wait random(0, 2)s
    attempt 3: wait random(0, 4)s
    attempt 4: wait random(0, 8)s
    ...
  Prevents all clients from hammering server simultaneously
```

---

## gRPC Streaming Connection Management

gRPC streams have unique characteristics: they run over HTTP/2 streams on top of one TCP connection:

```
gRPC bidirectional stream:
  ┌────────────────────────────────────────────────┐
  │  HTTP/2 TCP connection                          │
  │  ┌─────────────────────────────────────────┐   │
  │  │  Stream 1: user_id=123 watch events     │   │
  │  │  Stream 2: user_id=456 watch events     │   │
  │  │  ...                                     │   │
  │  └─────────────────────────────────────────┘   │
  └────────────────────────────────────────────────┘

  N users' watch streams on a small number of TCP connections
  (HTTP/2 multiplexing — much more efficient than N TCP connections)

  gRPC max concurrent streams: typically 100-1000 per connection
  → 1,000 clients on 10 TCP connections vs 1,000 TCP connections
```

---

## Summary: Trade-off Matrix

| Mechanism | Connection Cost | Latency | Complexity | Best For |
|-----------|----------------|---------|------------|----------|
| Short polling | Zero (on-demand) | High (1 poll interval) | Low | Infrequent, non-critical updates |
| Long polling | 1 conn per client | Medium (~30s max) | Medium | Moderate frequency, simple infra |
| SSE | Low (1 HTTP stream) | Low (immediate push) | Low | Read-only feeds, dashboards |
| WebSocket | Medium (~150KB RAM) | Low (full-duplex) | High | Chat, collaboration, gaming |
| gRPC streaming | Low (HTTP/2 multiplex) | Low | Medium | Internal service streaming |
| WebRTC | Low (P2P) | Very low (P2P UDP) | Very high | Video/audio calls |

---

## Interview Quick Answers

- **How do you scale to 1 million WebSocket connections?** — Distribute connections across a server cluster; use Redis pub/sub or a message broker for cross-server message routing.
- **What happens to WebSocket connections during a deployment?** — They drop unless you implement graceful draining: stop accepting new connections, send close frames, wait for clients to reconnect to other nodes.
- **Why does connection pooling exist for HTTP/REST?** — Establishing a new TCP+TLS connection costs 2-3 RTTs (~1-3ms). Pooling reuses connections to amortize this setup cost.
