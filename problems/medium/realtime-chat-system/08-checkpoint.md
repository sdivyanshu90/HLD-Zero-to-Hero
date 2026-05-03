# Step 8 — Checkpoint & Interview Q&A

**Q1: Why use WebSockets instead of HTTP polling for chat?**
> HTTP polling wastes bandwidth (empty responses) and has high latency (up to poll interval). Long-polling is better but still has per-request overhead. WebSocket establishes a persistent full-duplex connection — server pushes messages immediately with < 5ms overhead.

**Q2: How does a message reach a user connected to a different chat server?**
> Chat servers subscribe to Redis Pub/Sub (or Kafka) topics keyed by user_id. When Server 1 receives a message for user B (connected to Server 2), it publishes to topic `user:{B_id}`. Server 2's subscriber receives it and pushes via the WebSocket connection.

**Q3: How is user presence (online/offline) implemented?**
> Each connected client sends a heartbeat every 30s. Server writes `presence:{user_id} = {server_id}` in Redis with 45s TTL. TTL expiry = offline. On disconnect event, server deletes the key immediately. Followers subscribe to presence changes via Redis keyspace notifications.

**Q4: How do you handle message ordering in group chats?**
> Messages are stored in Cassandra with TIMEUUID as the clustering key. TIMEUUID is time-sortable and globally unique. Within a conversation partition, ordering is deterministic. For the client, messages are rendered sorted by message_id. Slight (< 1ms) out-of-order delivery from network jitter is visually corrected by client-side sort.

**Q5: How would you scale to support groups with 100K members?**
> Group fan-out becomes expensive. Solutions: (1) Use Kafka with conversation_id as partition key — consumers fan out to members. (2) Segment large groups — shard members into sub-groups, fan out to sub-group leaders. (3) Pull model for large groups — clients poll for new messages instead of server push (WhatsApp uses this for large groups).
