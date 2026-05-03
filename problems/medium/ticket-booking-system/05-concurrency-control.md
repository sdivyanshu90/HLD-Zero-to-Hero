# Step 5 — Concurrency Control

## The Problem: Race Condition

```
T1: Check seat_A → available
T2: Check seat_A → available
T1: Book seat_A  → ✓ (booked)
T2: Book seat_A  → ✓ (double-booked!)
```

## Solution 1: Redis Distributed Lock (Recommended for Flash Sales)

```python
def try_reserve_seat(seat_id: str, user_id: str, ttl_sec: int = 600):
    lock_key = f"seat_lock:{seat_id}"
    hold_key = f"seat_hold:{seat_id}"
    
    # Atomic: SET lock NX EX 600
    # Only one user wins this race
    if not redis.set(lock_key, user_id, nx=True, ex=ttl_sec):
        return {"status": "UNAVAILABLE", "reason": "Seat already held"}
    
    # Lock acquired — write to DB
    db.execute(
        "UPDATE seats SET status='HELD', user_id=? WHERE seat_id=? AND status='AVAILABLE'",
        user_id, seat_id
    )
    
    return {"status": "HELD", "expires_in_sec": ttl_sec}
```

## Solution 2: Database Optimistic Locking

```sql
-- version column prevents concurrent updates
UPDATE seats
SET status='HELD', user_id=?, version=version+1
WHERE seat_id=?
  AND status='AVAILABLE'
  AND version=?;   -- if 0 rows affected → another transaction won
```

Best for: low contention scenarios (most seats available).

## Solution 3: Pessimistic Lock (SELECT FOR UPDATE)

```sql
BEGIN;
SELECT seat_id, status FROM seats
WHERE seat_id = ? FOR UPDATE;  -- acquires row lock

-- now we have exclusive lock
IF status = 'AVAILABLE' THEN
    UPDATE seats SET status='HELD', user_id=? WHERE seat_id=?;
END IF;
COMMIT;
```

Best for: high contention, correctness critical.  
**Problem:** Long transactions block other transactions on same row.

## Two-Phase Hold Pattern (Production)

```
Phase 1: Hold (Redis NX, 10 min TTL)
  Fast, in-memory
  Prevents double-hold
  
Phase 2: Confirm (DB transaction after payment)
  Durable
  Only if hold is still valid

Phase 1.5: Payment processing
  ~3-5 seconds
  Hold still valid if < 10 min
  
On payment fail: Release Redis lock (allow next user to hold)
On hold expire:  Cron job re-marks seat as AVAILABLE in DB
```

## Inventory Bucket Optimization (Flash Sales)

```
Problem: 100K users request 10K seats simultaneously
         → 10K DB rows, each getting locked independently

Optimization: Inventory counters
  Redis: DECRBY available_seats:{event_id} 1
  if result < 0: INCRBY available_seats:{event_id} 1; deny
  
  Only proceed to individual seat lock if counter > 0
  → Filters 90K "no seats" cases before DB even touched
```

## Comparison

| Approach | Throughput | Consistency | Best For |
|----------|------------|-------------|---------|
| Redis NX lock | Very High | Strong | Flash sales, high contention |
| Optimistic Lock (DB) | High | Strong | Low contention |
| Pessimistic Lock (FOR UPDATE) | Medium | Strongest | Small events, correctness critical |
| Inventory counter | Extreme | Eventual | Pre-filter for flash sales |
