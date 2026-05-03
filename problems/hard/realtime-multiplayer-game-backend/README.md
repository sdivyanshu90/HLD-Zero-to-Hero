# Realtime Multiplayer Game Backend — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** UDP, authoritative-server, client-prediction, lag-compensation, ECS  
**Companies:** Riot Games, Epic Games, Valve, Activision

---

## Problem Statement

Design a real-time multiplayer game backend (like a battle royale or FPS) that:
- Supports 100 players in a single game instance with < 50ms state sync
- Uses an authoritative game server to prevent cheating
- Implements client-side prediction and server reconciliation
- Handles 100K concurrent game sessions globally

---

## Architecture Diagram

```
Players (game clients)
    │  UDP position updates (60 Hz)
    │  TCP/WS game events (spawn, shoot, chat)
    ▼
┌──────────────────────────────────────┐
│  Authoritative Game Server           │
│  ECS: entities + components          │
│  Physics + collision (server-side)   │
│  Lag compensation (rewind state)     │
└──────────────┬───────────────────────┘
               │ 60 Hz state broadcast
               ▼
         All 100 players
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 ┌──────┐  ┌──────┐  ┌──────────┐
 │Match │  │Leaver│  │Analytics │
 │DB    │  │board │  │(Kafka)   │
 └──────┘  └──────┘  └──────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Session and Matchmaking Model](02-session-and-matchmaking-model.md)
3. [Realtime State Synchronization](03-realtime-state-synchronization.md)
4. [Region Placement and Latency](04-region-placement-and-latency.md)
5. [Authoritative Server and Cheat Control](05-authoritative-server-and-cheat-control.md)
6. [Persistence and Reconnect](06-persistence-and-reconnect.md)
7. [Scaling Hot Matches and Failures](07-scaling-hot-matches-and-failures.md)
8. [Checkpoint](08-checkpoint.md)
