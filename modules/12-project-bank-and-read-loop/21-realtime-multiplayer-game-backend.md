# Cheat Sheet: Realtime Multiplayer Game Backend

## Scale (BoE)
```
Concurrent players: 10M (Fortnite scale)
Players per game room: 100
Concurrent game rooms: 100K
Game state updates per room: 60 state snapshots/second (60 fps)
Total state updates/second: 100K rooms × 60 = 6M state updates/second
Per-player messages per second: 60 × 100 players = 6,000 events/room
Total inbound events: 100K × 6K = 600M events/second → very high!
```

## Why UDP (Not TCP)?

```
TCP issues for gaming:
  Head-of-line blocking: one lost packet blocks ALL subsequent packets
  Retransmission delay: lost packet retransmitted → 100ms+ latency spike
  Player "teleports": after lag spike, player position jumps
  
UDP advantages:
  No retransmission: just drop lost packets
  No ordering guarantee: latest position update replaces stale one
  Much lower latency under loss: ~20ms vs ~100ms+ with TCP loss

For game state:
  Lost position update = fine (next update arrives 16ms later)
  Lost "fire weapon" event = BAD (must not lose)
  
  Solution: UDP for real-time position + TCP/WebSocket for important events (kills, pickups)
  Or: QUIC (UDP-based, avoids HOL blocking, has streams with different reliability)
```

## Game Server Architecture

```
Global:
  Player ──UDP──▶ Game Server Region (AWS GameLift or custom)
                        │
                 Matchmaking Service
                 (find N players in same region with similar skill)
                        │
                 Provision Game Room Instance
                        │
                 All 100 players connect to same game server

Game Room Server (authoritative):
  Receives: player input events (move, shoot, jump)
  Computes: game state (positions, health, inventory)
  Broadcasts: state snapshot every 16ms (60 fps) to all 100 players
  
  Authoritative server: server is the truth, client is approximate prediction
  Client-side prediction: client predicts movement locally (feels responsive)
  Server reconciliation: server corrects client if prediction was wrong
```

## State Synchronization

```
Full state sync (every tick):
  Server sends ENTIRE game state every 16ms to all players
  100 players × 1 KB state = 100 KB × 60/s = 6 MB/s outbound per room
  × 100K rooms = 600 GB/s → too much!
  
Delta compression:
  Only send CHANGES since last acknowledged state
  Player was at (100, 200) last tick, now at (101, 200) → send delta (+1, 0)
  Typical delta: ~100 bytes per player × 100 players = 10 KB/tick
  10 KB × 60/s × 100K rooms = 60 GB/s (still large but manageable)
  
Interest management:
  Only broadcast nearby players to each player (within render distance)
  Player sees 20 nearby players out of 100 → 5× bandwidth reduction
```

## Lag Compensation

```
Problem: Player A shoots at Player B, but due to 50ms latency, 
         Player B has already moved by the time shot reaches server.
         Server sees shot miss (Player B's current position) but
         shot was aimed correctly at B's position FROM A's perspective.

Solution: Rewind time
  Server stores last 200ms of game state history
  When shot arrives with timestamp T:
    Rewind world state to time T (A's perspective)
    Check hit/miss in the rewound state
    If hit: register hit (even though B has already moved)
  
  This favors the shooter's experience over the target's
  (shooter sees what they aimed at; target may get shot from behind where they already moved)
```

## Unique Trick
Entity Component System (ECS): game state represented as components (position, health, velocity) attached to entities (players, enemies, bullets). The game tick loop is a pure data transformation: input components → physics system → new position components → collision system → update health components. This architecture allows game state to be snapshotted, diff-compressed, and replayed efficiently.
