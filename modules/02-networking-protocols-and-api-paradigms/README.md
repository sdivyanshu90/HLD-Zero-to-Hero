# Module 02: Networking Protocols and API Paradigms

## Overview

Networking is the connective tissue of distributed systems. Every byte your services exchange traverses the network stack, and the protocol choices you make determine latency, scalability, and complexity.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│             MODULE 02 LEARNING MAP                              │
│                                                                  │
│  01-osi-layer-4-and-layer-7                                     │
│     └── L4 vs L7 load balancing, what each can route on        │
│         TCP connection lifecycle and handshake cost             │
│                    │                                            │
│                    ▼                                            │
│  02-tcp-vs-udp                                                  │
│     └── Reliability vs speed, when to choose each              │
│         QUIC: best of both worlds (HTTP/3)                      │
│                    │                                            │
│                    ▼                                            │
│  03-http-evolution                                              │
│     └── HTTP/1.1 HOL → HTTP/2 multiplexing → HTTP/3 QUIC       │
│         Header compression, server push, 0-RTT                 │
│                    │                                            │
│                    ▼                                            │
│  04-api-paradigms                                               │
│     └── REST, GraphQL, gRPC — strengths and trade-offs         │
│         When to use each; N+1 problem; proto vs JSON           │
│                    │                                            │
│                    ▼                                            │
│  05-realtime-delivery                                           │
│     └── Polling → Long poll → SSE → WebSocket → WebRTC        │
│         Latency, scalability, complexity at each tier          │
│                    │                                            │
│                    ▼                                            │
│  06-connection-holding-trade-offs                               │
│     └── Resource cost per connection, heartbeats               │
│         Scaling WebSocket, graceful draining                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Key Decision Framework

```
Choosing a protocol:
  Internal service-to-service, high volume → gRPC (HTTP/2, binary)
  Public API, external clients             → REST (HTTP/1.1+, JSON)
  Mobile/flexible queries                  → GraphQL
  Server push only                         → SSE
  Bidirectional real-time                  → WebSocket
  Real-time audio/video                    → WebRTC

Choosing a transport:
  Need reliability + ordering              → TCP
  Need low latency, can tolerate loss      → UDP
  Need reliability + no HOL blocking       → QUIC
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-osi-layer-4-and-layer-7.md](01-osi-layer-4-and-layer-7.md) | L4 vs L7 load balancing, TCP lifecycle |
| [02-tcp-vs-udp.md](02-tcp-vs-udp.md) | TCP reliability, UDP use cases, QUIC |
| [03-http-evolution.md](03-http-evolution.md) | HTTP/1.1 → HTTP/2 → HTTP/3 |
| [04-api-paradigms.md](04-api-paradigms.md) | REST, GraphQL, gRPC comparison |
| [05-realtime-delivery.md](05-realtime-delivery.md) | Polling, SSE, WebSocket, WebRTC |
| [06-connection-holding-trade-offs.md](06-connection-holding-trade-offs.md) | Scaling persistent connections |
| [07-checkpoint.md](07-checkpoint.md) | Self-test questions |
