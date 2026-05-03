# Real-Time Chat System — System Design Walkthrough

**Difficulty:** Medium  
**Tags:** WebSocket, Cassandra, Redis pub/sub, presence, fan-out  
**Companies:** WhatsApp, Slack, Discord, Telegram

---

## Problem Statement

Design a scalable real-time chat system that:
- Supports 1:1 and group chat (up to 500 members)
- Delivers messages with < 100ms latency
- Stores message history durably
- Shows online/offline presence
- Handles 50 M DAU with 20 messages/day per user

---

## Architecture Diagram

```
Client A (WebSocket)                Client B (WebSocket)
    │                                      │
    ▼                                      ▼
┌─────────────────┐              ┌─────────────────┐
│ Chat Server 1   │              │ Chat Server 2   │
│ (connection mgr)│              │ (connection mgr)│
└────────┬────────┘              └────────┬────────┘
         │                                │
         └──────────────┬─────────────────┘
                        │
               ┌────────▼────────┐
               │  Redis Pub/Sub  │  cross-server message routing
               │  (or Kafka)     │
               └────────┬────────┘
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
   ┌────────────┐ ┌──────────┐ ┌────────────┐
   │ Cassandra  │ │  Redis   │ │  Service   │
   │ (messages) │ │(presence)│ │ Discovery  │
   └────────────┘ └──────────┘ └────────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic and Message Model](02-traffic-and-message-model.md)
3. [API and Realtime Channel](03-api-and-realtime-channel.md)
4. [Message Storage and Ordering](04-message-storage-and-ordering.md)
5. [Presence and Delivery Semantics](05-presence-and-delivery-semantics.md)
6. [Group Chat and Fan-Out](06-group-chat-and-fan-out.md)
7. [Scaling and Failure Modes](07-scaling-and-failure-modes.md)
8. [Checkpoint](08-checkpoint.md)
