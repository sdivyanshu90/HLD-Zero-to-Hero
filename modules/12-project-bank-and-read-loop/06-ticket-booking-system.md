# Cheat Sheet: Ticket Booking System

## Scale (BoE)
```
Events: 10K concurrent events at peak
Users: 100K concurrent users trying to book the same event
Ticket inventory: 50K seats per event
Booking QPS: 100K concurrent users × 1 attempt/5s = 20K booking requests/sec peak
```

## System Diagram
```
Client ──▶ API Gateway ──▶ Booking Service
                                │
                    ┌───────────┼────────────────┐
                    ▼           ▼                ▼
              Redis            PostgreSQL       Kafka
              (seat lock)      (inventory)      (async notif)
              
Write path:
  1. User selects seat
  2. Redis SET "seat:{event}:{seat}" "user:123" NX EX 600  (10-min hold)
  3. If NX fails → seat taken → show error
  4. User provides payment details
  5. BEGIN TRANSACTION
     CHECK seat lock in Redis still held by user
     DEDUCT from inventory
     INSERT booking record
     COMMIT
  6. DELETE Redis lock key
  7. Send confirmation → Kafka → Email Service
```

## Key Design Decisions

**1. Concurrency control:**
- Optimistic locking: read version, update WHERE version = N, check affected rows
  - Good for low contention, many retries under high contention
- Pessimistic locking: SELECT FOR UPDATE (DB row lock)
  - Good for very high contention (concert tickets!)
- **Two-phase: Redis NX lock (fast hold) + DB transaction (commit)**
  - Redis: instant hold with TTL auto-release → reduces DB contention
  - DB: final truth, prevents double-booking

**2. Inventory management:**
- Store available_seats as atomic counter (Redis DECR or DB UPDATE ... RETURNING)
- Pre-check: DECR available → if result < 0: INCR back + reject (no seat available)

**3. Seat expiry:**
- "Hold for 10 minutes then release" → Redis TTL auto-expiry handles this
- Background job: find expired holds in DB, mark as available

## Bottlenecks
1. Inventory: single row per event = hot row under concurrent update (DB lock contention)
   - Solution: partition inventory into buckets (100 rows of 50 seats each)
2. Read amplification during flash sale: cache event/seat map in Redis

## Unique Trick
The two-phase hold pattern: Redis NX lock takes the seat "instantly" without a DB write, reducing DB contention dramatically. The DB transaction is the final arbiter, but 99% of "seat taken" conflicts are caught by Redis without hitting the DB.
