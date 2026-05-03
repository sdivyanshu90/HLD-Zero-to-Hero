# Step 4 — Message Storage and Ordering

## Why Cassandra?

```
Requirements:
  - Very high write throughput (35K msg/sec)
  - Time-ordered message history per conversation
  - Linear horizontal scaling
  - No need for complex SQL joins

Cassandra fits:
  - Wide-row model: partition by conversation, cluster by time
  - Append-only writes (chat history never updated)
  - Tunable consistency (QUORUM for critical reads)
```

## Schema Design

```sql
CREATE TABLE messages (
    conversation_id UUID,
    message_id      TIMEUUID,       -- time-sorted UUID (combines time + unique)
    sender_id       BIGINT,
    content         TEXT,
    message_type    TEXT,           -- text, image, file, system
    status          TEXT,           -- sent, delivered, seen
    created_at      TIMESTAMP,

    PRIMARY KEY (conversation_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC)
  AND default_time_to_live = 157680000;  -- 5 years TTL
```

## Message ID: TIMEUUID

```
TIMEUUID (type 1 UUID):
  60-bit timestamp (100ns precision from Oct 1582)
  + 14-bit clock sequence (prevents duplicates at same timestamp)
  + 48-bit node ID (MAC address or random)

Benefits:
  - Time-sortable (same ordering as created_at)
  - Globally unique without coordination
  - Cassandra TIMEUUID functions: now(), minTimeuuid(), maxTimeuuid()

Query last 50 messages:
  SELECT * FROM messages
  WHERE conversation_id = ?
  AND message_id > maxTimeuuid(now() - 7 days)
  ORDER BY message_id DESC
  LIMIT 50;
```

## Message Ordering Guarantee

```
Within Cassandra partition (conversation):
  Ordering by TIMEUUID is total and deterministic

Across concurrent sends from different clients:
  Two clients send at exact same ms →
    TIMEUUID clock_seq differs → still unique and ordered

Clock skew across servers:
  Cassandra uses server-side timestamp, not client
  Chat server inserts with NOW() → Cassandra node timestamp
  Slight reordering possible (< 1ms) → acceptable for chat
```
