# Cheat Sheet: Realtime Chat System

## Scale (BoE)
```
Users: 500M registered, 50M DAU (WhatsApp scale)
Messages per day: 100B messages/day (50M × 2000 msgs/day)
Write QPS: 100B / 86,400 ≈ 1.16M messages/second (across all servers)
Concurrent connections: 50M (WebSocket per user)
```

## System Diagram
```
User A ──WebSocket──▶ Chat Server 1 ──▶ Message DB (Cassandra)
                            │
                     Message Router
                     (which server holds User B's connection?)
                            │
                     Connection Registry (Redis)
                     user_id → server_id
                            │
               ┌────────────┘
               ▼
        Chat Server 2 ──WebSocket──▶ User B (deliver message)
```

## Connection Management

```
WebSocket connections:
  50M concurrent connections across N chat servers
  1 server handles ~50K connections (limited by file descriptors + memory)
  Servers needed: 50M / 50K = 1,000 chat servers
  
  Each server maintains: in-memory map {user_id: websocket_conn}
  
Connection registry (Redis):
  user:12345 → server_id=chat-server-47
  When User A sends to User B: 
    1. Lookup B's server in Redis
    2. Forward message to chat-server-47 via internal HTTP/gRPC
    3. chat-server-47 delivers via WebSocket to B's connection

Offline delivery (User B is offline):
  Push notification via APNS/FCM
  Message stored in DB → delivered on next connection
```

## Message Storage

```
Schema (Cassandra - wide-column, optimized for message history):
  Table: messages
    Partition key: conversation_id (all msgs in a conversation together)
    Clustering key: message_id DESC (sorted, newest first)
    
    conversation_id  UUID
    message_id       TIMEUUID  (time-sortable UUID)
    sender_id        BIGINT
    content          TEXT
    status           ENUM (sent, delivered, read)
    created_at       TIMESTAMP
  
  Query patterns:
    "Load last 50 messages for conversation X" →
    SELECT * FROM messages WHERE conversation_id = X LIMIT 50
    (single partition, sequential scan → fast)
```

## Key Design Decisions

**1. Message ordering:**
- Within a conversation: monotonic sequence number per conversation (or TIMEUUID)
- Across conversations: no global ordering needed

**2. Message status (sent/delivered/read):**
- Sent: stored in DB
- Delivered: ACK when recipient's WebSocket receives it
- Read: receipt sent when user reads/opens conversation

**3. Group chat fan-out:**
- Small groups (< 100): fan-out on write (send to all members' queues)
- Large groups (100+): fan-out on read (members pull from group message log)

## Unique Trick
The connection registry in Redis is the lookup table for "which server holds this user's WebSocket connection." This is the core coordination mechanism in a distributed chat system. Without it, you can't route a message from Server 1 (where sender is connected) to Server 2 (where recipient is connected).
