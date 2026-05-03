# Module 02 Checkpoint: Networking Protocols and API Paradigms

## Questions to Test Your Understanding

---

**Q1.** A request enters an L4 load balancer, then an L7 load balancer. Where does TLS termination happen, and why?

> **Answer:** TLS terminates at the **L7 load balancer**. L4 (like AWS NLB) sees only TCP packets and cannot decrypt TLS. L7 (like AWS ALB or Nginx) terminates TLS, reads the HTTP request, and routes based on headers/paths. After the L7 LB, traffic to backend servers may be re-encrypted (mTLS) or sent as plain HTTP depending on your security posture.

---

**Q2.** A gRPC service processes 100,000 requests/second. How many TCP connections does it typically hold open compared to HTTP/1.1?

> **Answer:** HTTP/1.1 at 100K req/s might need 100K concurrent open connections (one per in-flight request). gRPC over HTTP/2 uses one TCP connection per client–server pair, with up to 100–1,000 concurrent streams multiplexed on it. For 100K req/s from 1,000 clients: HTTP/1.1 = ~100K connections; gRPC = ~1,000 connections (100 streams each). ~100× fewer file descriptors.

---

**Q3.** You need to push live updates to 500,000 browser clients. SSE vs WebSocket — which do you choose and why?

> **Answer:** SSE is preferable if updates are server-to-client only (news feed, scores, stock prices). SSE is simpler (standard HTTP, works through all proxies), has native auto-reconnect, and is easier to scale behind a CDN. WebSocket is better if clients also send data (chat, collaboration). For 500K connections, both require async server architecture and horizontal scaling with Redis pub/sub.

---

**Q4.** What is HOL blocking in the context of HTTP/2 over TCP?

> **Answer:** Even though HTTP/2 multiplexes multiple streams over one TCP connection, TCP must deliver packets in order. If a TCP segment carrying stream 1's data is lost, all streams stall waiting for retransmission — even streams 2, 3, 4 whose data arrived fine. HTTP/3 (QUIC) solves this: QUIC implements per-stream reliability so a lost packet only stalls the stream it belongs to.

---

**Q5.** Design a chat system that needs to handle 1 million concurrent online users, where any user can send to any other user.

> Key decisions to discuss:
> - WebSocket server farm (each server handles 10K–50K connections)
> - Redis pub/sub or Kafka for cross-server message routing
> - User-to-server mapping in Redis (user_id → ws_server_id)
> - Message persistence in a database (Cassandra for write-heavy chat history)
> - Presence/heartbeat service for online status
> - Exponential backoff on reconnect to prevent thundering herd

---

## Numbers to Remember

| Protocol | Typical Setup Overhead | Use Case |
|----------|----------------------|----------|
| HTTP/1.1 REST | 1-3ms (new connection) | Public APIs |
| HTTP/2 gRPC | ~1ms (first request) | Internal microservices |
| WebSocket | ~1ms (upgrade) then 0 | Real-time apps |
| SSE | ~1ms (HTTP open) then 0 | Server push feeds |
| QUIC/HTTP/3 | 0.5ms (1-RTT) or 0ms (0-RTT) | Mobile, high-loss networks |

---

## Checklist

- [ ] L4 vs L7: what each layer can see and route on
- [ ] TCP 3-way handshake cost (~1.5 RTT) and why connection pooling matters
- [ ] HTTP/1.1 HOL blocking and the 6-connection workaround
- [ ] HTTP/2 multiplexing, HPACK header compression
- [ ] HTTP/3 QUIC: solves TCP HOL blocking, 0-RTT, connection migration
- [ ] REST: stateless, cacheable, universal but over/under-fetching
- [ ] GraphQL: client-driven, eliminates over-fetching, hard to cache
- [ ] gRPC: binary, HTTP/2, streaming, 2-5× faster than REST/JSON
- [ ] Polling → Long polling → SSE → WebSocket: progressive complexity
- [ ] WebSocket scaling: sticky LB + Redis pub/sub for cross-server routing
