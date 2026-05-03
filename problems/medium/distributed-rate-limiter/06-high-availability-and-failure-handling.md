# Step 6 — High Availability and Failure Handling

## Redis Failure Modes

### Fail Open (recommended for most APIs)

```python
try:
    result = redis.eval(LUA_SCRIPT, ...)
    return result
except RedisConnectionError:
    logger.warning("Rate limiter unavailable, failing open")
    return RateLimitResult(allowed=True, remaining=-1, ...)
```

**Rationale:** A rate limiter outage shouldn't take down the entire service. Brief bursts during outage are acceptable.

### Fail Closed (for sensitive APIs)

```python
except RedisConnectionError:
    return RateLimitResult(allowed=False, retry_after=5, ...)
```

Use for payment APIs, admin endpoints where correctness > availability.

## Local Cache Fallback

```
Architecture with local fallback:

┌────────────────────────────┐
│  App Server                │
│  ┌──────────────────────┐  │
│  │ Local Rate Limiter   │  │  in-process (Caffeine / dict)
│  │ (approximate, 1s TTL)│  │  absorbs 90% of checks
│  └──────────┬───────────┘  │
│             │ sync every 1s│
└─────────────┼──────────────┘
              │
         ┌────▼──────────────┐
         │   Redis Cluster   │  global state
         └───────────────────┘
```

## Redis Replication for HA

```
Master-Replica setup:
  Master accepts writes (INCR, EXPIRE)
  Replica serves reads (GET for non-atomic checks)

On master failure:
  Redis Sentinel promotes replica (~1-2s)
  During failover: brief fail-open period
  
Redis Cluster:
  Automatic failover per slot
  Each slot has 1 master + N replicas
  Writes ack from master only (replica is async)
  Race window: master dies after INCR but before replica gets it
  → slightly under-counted, acceptable for soft limits
```

## Rate Limiting for Distributed Workers

```
Problem: 10 app servers each with local token bucket
         each thinks it can send 100 req/min
         → 10 × 100 = 1000 req/min actual

Solutions:
  1. Centralised Redis (strong consistency, add latency)
  2. Gossip protocol (eventual, share counters peer-to-peer)
  3. Token allocation: global 100 req/min / 10 servers = 10 each
     → re-allocate if servers join/leave (via ZooKeeper)
```
