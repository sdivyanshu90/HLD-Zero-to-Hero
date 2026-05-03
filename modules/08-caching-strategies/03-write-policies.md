# Cache Write Policies

## The Core Problem: Cache-Database Consistency

A cache is a copy of database data. Whenever data changes, the cache and database can diverge. Write policies define how and when cache and database are updated.

---

## Write-Through

Write to cache and database simultaneously:

```
Write-Through Flow:
  ┌──────────┐         ┌───────────┐         ┌──────────┐
  │  Client  │──write──▶   Cache   │──write──▶ Database │
  │          │◄──ACK───│           │◄──ACK───│          │
  └──────────┘         └───────────┘         └──────────┘

  Both cache and DB are written atomically before ACKing client.

Pseudocode:
  def update_user(user_id, data):
      db.update(f"users:{user_id}", data)  # write to DB first
      cache.set(f"user:{user_id}", data, ttl=3600)  # then cache
      return success

Advantages:
  ✓ Cache always consistent with DB (never stale for written keys)
  ✓ Simple to reason about (cache = DB for all recent writes)
  ✓ No data loss if cache fails (data always in DB)

Disadvantages:
  ✗ Higher write latency (must wait for both cache AND DB write)
  ✗ Cache may fill with entries that are never read again ("write amplification")
     → Solution: set TTL on cache entries
  ✗ Adds cache write overhead to every DB write even if reads are rare

Best for: data that is written AND read frequently, consistency is important
Examples: user profile updates, product price changes
```

---

## Write-Behind (Write-Back)

Write to cache immediately, update database asynchronously:

```
Write-Behind Flow:
  ┌──────────┐         ┌───────────┐
  │  Client  │──write──▶   Cache   │──ACK──▶ Client  (fast!)
  │          │         └─────┬─────┘
  └──────────┘               │ async (batch, periodic)
                             ▼
                        ┌──────────┐
                        │ Database │
                        └──────────┘

Pseudocode:
  def update_user(user_id, data):
      cache.set(f"user:{user_id}", data)  # write to cache
      write_queue.push(f"users:{user_id}", data)  # async DB write
      return success  # ACK immediately!
  
  background_worker:
      while True:
          batch = write_queue.pop(100)  # batch 100 writes
          db.batch_update(batch)        # single DB round trip for 100 writes
          sleep(100ms)

Advantages:
  ✓ Much lower write latency (only cache write in critical path)
  ✓ DB write batching → much higher DB write throughput
  ✓ Absorb write bursts (queue smooths spikes)

Disadvantages:
  ✗ DATA LOSS RISK: if cache fails before async write → data lost!
  ✗ Cache and DB temporarily inconsistent (replication lag)
  ✗ Complex error handling (what if DB write fails in background?)

Best for: non-critical data where some loss is acceptable, high write throughput
Examples: view counters, user activity logs, analytics events, like counts
NOT for: financial transactions, orders, inventory
```

---

## Cache-Aside (Lazy Loading)

Application code manages cache explicitly; database is the source of truth:

```
Cache-Aside Read Flow:
  ┌──────────┐    1. read    ┌───────────┐
  │  Client  │──────────────▶│   Cache   │
  │          │               └─────┬─────┘
  │          │◄──hit (fast!)       │ miss
  │          │               2. read from DB
  │          │               ┌──────────┐
  │          │◄──slow read───│ Database │
  │          │         3. update cache  │
  │          │               └──────────┘
  └──────────┘

Cache-Aside Write Flow:
  Write to DB → INVALIDATE (delete) the cache entry
  Next read: cache miss → load from DB → repopulate cache

Pseudocode:
  def get_user(user_id):
      cached = cache.get(f"user:{user_id}")
      if cached:
          return cached
      user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
      cache.set(f"user:{user_id}", user, ttl=3600)
      return user
  
  def update_user(user_id, data):
      db.update(f"users:{user_id}", data)
      cache.delete(f"user:{user_id}")  # INVALIDATE, not update

Advantages:
  ✓ Simple to implement (no cache dependency on writes)
  ✓ Cache only populated for data that's actually read
  ✓ DB remains source of truth (cache failure = just slower reads)
  ✓ Resilient: application works even if cache is down

Disadvantages:
  ✗ Cache miss on first access (cold start)
  ✗ Race condition: update DB, delete cache, another request refills with old data
  ✗ Data in cache can be stale (TTL limits this)

Best for: read-heavy workloads, simple implementations, when cache is purely an optimization
Most common pattern: this is what most applications use!
```

---

## Write-Around

Write directly to database, bypass cache:

```
Write-Around:
  Write: Client → DB (cache bypassed)
  Read:  Client → Cache → DB (standard cache-aside)

Use when:
  Written data is unlikely to be read soon
  Avoids polluting cache with write-once-read-never data
  Examples: large data loads, bulk imports, log data

Combined with cache-aside for reads: very simple, clean pattern
```

---

## The Thundering Herd Problem

When a popular cache entry expires, many requests simultaneously miss and all hit the database:

```
Timeline:
  t=0: cache.set("popular_product:123", ..., ttl=3600)
  t=3600: TTL expires → cache entry deleted
  t=3600+: 10,000 requests arrive simultaneously
    → All miss cache → ALL 10,000 hit database simultaneously!
    → DB gets 10,000× normal load → overloaded → slow → timeouts → cascade
```

### Solutions

```
1. Cache lock (mutex / "dog pile" prevention):
   def get_product(product_id):
       cached = cache.get(f"product:{product_id}")
       if cached: return cached
       
       # Only one process recomputes, others wait
       lock_key = f"lock:product:{product_id}"
       if cache.set(lock_key, "1", NX=True, EX=5):  # acquired lock
           try:
               product = db.get_product(product_id)
               cache.set(f"product:{product_id}", product, ttl=3600)
               return product
           finally:
               cache.delete(lock_key)
       else:
           # Another process is recomputing, wait briefly and retry
           time.sleep(0.1)
           return get_product(product_id)  # recursive retry

2. Cache staggering (jitter on TTL):
   cache.set(key, value, ttl=3600 + random(0, 300))
   → Prevents all cache entries from expiring at the same moment

3. Background refresh:
   When TTL is at 80%: asynchronously refresh in background
   → Cache entry always "warm", never expires during a request
   Caffeine: refreshAfterWrite + expireAfterWrite (different durations)
```

---

## Interview Quick Answers

- **What is the difference between cache-aside and write-through?** — Cache-aside: application explicitly checks cache, then DB. On write, invalidates cache entry. Simple, resilient to cache failure. Write-through: cache layer sits between app and DB, all reads/writes go through cache. Keeps cache always populated but adds write latency.
- **What is write-behind caching and what is the risk?** — Write to cache immediately, batch-write to DB asynchronously. Risk: if cache crashes before DB write, data is lost. Only suitable for non-critical data (view counters, like counts, analytics).
- **How do you prevent thundering herd on cache expiry?** — Option 1: TTL jitter (random variance in expiry time). Option 2: mutex lock on cache miss (only one request recomputes, others wait). Option 3: background refresh before TTL expires (always keep cache warm).
