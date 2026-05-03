# Step 5 — Persistence Options

## Why Persist a Cache?

- **Warm restart:** After crash, cache is pre-loaded (no cold-start stampede)
- **Durable sessions:** User session data needs to survive node restarts
- **Primary store:** When cache IS the source of truth (no backing DB)

## Redis Persistence Modes

### RDB (Redis Database Snapshot)

```
SAVE 3600 1      # if ≥1 key changed in last hour, snapshot
SAVE 300 100     # if ≥100 keys changed in 5 min, snapshot
SAVE 60 10000    # if ≥10000 keys changed in 1 min, snapshot
```

```
┌──────────────┐   fork()    ┌──────────────┐
│   Redis      │ ─────────►  │  Child proc  │ writes .rdb file
│   (parent)   │             │  (snapshot)  │ atomically renamed
└──────────────┘             └──────────────┘
                                             (no blocking on parent)
```

**Pros:** Compact binary file, fast restart  
**Cons:** Data loss = last snapshot interval (up to 1h)

### AOF (Append-Only File)

```
Every write command is appended to aof file:
  *3
$3
SET
$5
hello
$5
world


fsync options:
  appendfsync always   → every write  (safest, slowest)
  appendfsync everysec → every second (default, ≤ 1s data loss)
  appendfsync no       → OS decides   (fastest, most data loss)
```

**AOF Rewrite:** Background compaction — replays all keys once:
```
SET a 1; SET a 2; SET a 3  →  compacts to  SET a 3
```

### Comparison

| Feature | RDB | AOF | Both (hybrid) |
|---------|-----|-----|---------------|
| Data loss on crash | Last snapshot | ≤ 1 second | ≤ 1 second |
| Restart speed | Fast (binary) | Slow (replay) | Fast |
| File size | Small | Large (grows) | Medium |
| Performance impact | Low (fork) | Low (everysec) | Low |
| Complexity | Simple | Moderate | Higher |

**Recommendation:** Use hybrid (RDB + AOF) for critical data.

## Memcached: No Persistence

Memcached is purely in-memory with no persistence. Cache misses always fall through to the backing DB. This is intentional — it keeps Memcached simpler and faster.
