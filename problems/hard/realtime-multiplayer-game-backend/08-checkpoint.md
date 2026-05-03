# Step 8 — Checkpoint & Interview Q&A

**Q1: Why UDP instead of TCP for game position updates?**
> TCP's head-of-line blocking: if packet N is lost, packets N+1, N+2... are buffered until N retransmits. For a position update 100ms later, the retransmitted old position is useless. UDP: dropped packets are simply gone; the next position update (16ms later) is received immediately. Games prefer fresh stale data over guaranteed old data. TCP is used for important events (kills, spawns) where reliability matters.

**Q2: What is client-side prediction and why is it needed?**
> Without prediction: player presses W, sends packet to server (50ms RTT), waits for server confirmation, then renders movement. Result: input lag of 50ms — game feels unresponsive. With prediction: client immediately moves the player locally based on input. When server confirms, if server position diverges (by > threshold), snap to server position (reconciliation). Players perceive zero input lag.

**Q3: How does lag compensation work for shooting?**
> When Player A shoots at Player B, the server receives A's "shoot" event 25ms late. Player B has moved in those 25ms. Without lag compensation: A aimed correctly at B's old position — misses. With lag compensation: server rewinds B's position back 25ms (to when A aimed), checks if the shot hit, applies damage. This requires storing a rolling buffer of all entity positions for the last ~200ms.

**Q4: How do you handle a game server crash mid-match?**
> (1) State checkpointed every 5 seconds to Redis (full serialized game state). (2) On server crash, matchmaking detects heartbeat failure within 10 seconds. (3) New server instance is provisioned; loads last checkpoint from Redis. (4) Players reconnect (reconnect token from initial auth). (5) 10-15 seconds of lost game state is accepted for robustness.

**Q5: How do you scale to 100K concurrent game sessions?**
> Each game session is an isolated process (or container). 100 players × 60 Hz state = 6 KB/s per session. 100K sessions = 600 MB/s total (manageable). Stateless matchmaking assigns sessions to available game server nodes. Kubernetes autoscaling provisions game server pods on-demand. Separate fleets per region (US/EU/APAC) for < 50ms latency.
