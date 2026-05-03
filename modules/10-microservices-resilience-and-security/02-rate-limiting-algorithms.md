# Rate Limiting Algorithms

## Why Rate Limit?

```
Without rate limiting:
  - DDoS: one bad client sends 10M requests → overwhelms your service
  - Fairness: one heavy user starves other users
  - Cost: runaway client causes huge cloud compute bill
  - Cascades: overloaded service → slow → queues fill → other services time out

Rate limiting answers: how many requests per unit time is a client allowed?
```

---

## Algorithm 1: Token Bucket

Conceptually: a bucket holds N tokens. Tokens added at rate R/second. Each request consumes 1 token. If bucket is empty: reject request.

```
Bucket: capacity = 10 tokens
Refill rate: 2 tokens/second

Token state timeline:
  t=0:  bucket=10 tokens (full)
  t=0:  5 requests arrive → consume 5 tokens → bucket=5
  t=0:  10 more requests arrive → consume 5, reject 5 (bucket empty)
  t=1:  +2 tokens added → bucket=2
  t=1:  1 request → consume 1 → bucket=1
  t=2:  +2 tokens → bucket=3 (capped at 10 max)

Properties:
  ✓ Allows burst up to bucket capacity (smooth burst handling)
  ✓ Average rate enforced: cannot exceed R tokens/sec sustained
  ✓ Simple and efficient

Redis implementation:
  val = redis.get("rate:{user_id}")
  if val is None:
      redis.setex("rate:{user_id}", WINDOW, CAPACITY)
      # allow request
  else:
      tokens = float(val)
      if tokens >= 1:
          redis.decrby("rate:{user_id}", 1)
          # allow request
      else:
          # reject (429 Too Many Requests)
  
  (Better: use Redis Lua script for atomicity)
```

---

## Algorithm 2: Leaky Bucket

Requests enter a queue (the bucket). Processed at a constant rate. Excess requests overflow (rejected or queued).

```
Leaky bucket:
  Bucket (queue): capacity = 100
  Drain rate: 10 requests/second (constant)
  
  t=0:  100 requests arrive → queue fills to 100
  t=0:  101st request → bucket overflow → rejected
  t=1:  10 requests drained → queue=90 → process 10 at constant rate
  
  Difference from Token Bucket:
    Token Bucket: burst allowed (consume all tokens instantly)
    Leaky Bucket: enforces smooth, constant output rate
    
  Use leaky bucket when you need smooth traffic for downstream (e.g., payment processor that wants steady rate)
  Use token bucket when you want to allow bursts within limits
```

---

## Algorithm 3: Fixed Window Counter

```
Divide time into fixed windows (e.g., each minute):
  Window: 12:00:00 - 12:00:59
  Counter: count requests in this window
  Limit: 100 requests per window

  Redis key: "rate:{user_id}:{minute}"
  INCR rate:alice:202312101200 → counter++
  If counter > 100: reject

  EXPIRE rate:alice:202312101200 60  (auto-cleanup)

Problem: boundary attack
  12:00:59: 100 requests (at window boundary)
  12:01:00: 100 requests (new window, counter reset!)
  → 200 requests in 2 seconds = 2× the intended limit!
```

---

## Algorithm 4: Sliding Window Log

```
Track timestamps of all requests in a sorted set:
  For each request:
    1. Remove timestamps older than now - window_size (1 minute)
    2. Count remaining entries in sorted set
    3. If count < limit: allow, add current timestamp
    4. Else: reject

Redis implementation:
  now = time.time()
  window_start = now - 60  # 1 minute window
  
  redis.execute_pipeline:
    ZREMRANGEBYSCORE "rate:{user_id}" 0 {window_start}
    ZCARD "rate:{user_id}"        → current count
    ZADD "rate:{user_id}" {now} {now}
    EXPIRE "rate:{user_id}" 60

Advantages: accurate sliding window, no boundary attack
Disadvantages: memory proportional to request count per user
  (1000 QPS user = 60,000 timestamps stored = significant memory)
```

---

## Algorithm 5: Sliding Window Counter (Hybrid)

Best of fixed window (memory efficient) + sliding window (no boundary attack):

```
Approximate sliding window using two adjacent fixed windows:

  Previous window count: prev_count
  Current window count: curr_count
  Time elapsed in current window: elapsed (0.0 to 1.0)
  
  Weighted estimate of requests in the last 60 seconds:
    estimated = prev_count * (1 - elapsed) + curr_count
  
  Example:
    Previous window (11:59): 80 requests
    Current window (12:00): 30 requests
    We're 40% through the current window (elapsed=0.4)
    
    Estimated = 80 * (1-0.4) + 30 = 80 * 0.6 + 30 = 48 + 30 = 78
    Limit = 100 → allow (78 < 100)

Advantages:
  ✓ Memory: only 2 counters per user (vs log-based: all timestamps)
  ✓ No boundary attack (weighted blending)
  ✓ Approximately accurate (~0.003% error in analysis)
  ✓ Used by Cloudflare, Stripe for high-scale rate limiting
```

---

## Distributed Rate Limiting

```
Problem: rate limit state must be shared across multiple API servers

  API Server 1 ──▶ Redis ←── API Server 2
  API Server 3 ──▶ Redis

  Redis INCR is atomic: safe for distributed counters
  
  But Redis round-trip adds ~0.5ms per request
  For 100K QPS: 100K Redis operations/second
  
  Optimization: local + global rate limiting
    Each API server maintains local counter (in-process)
    Local counter: allow up to limit/N locally (N = num servers)
    Periodically sync local count to Redis global counter
    Global check: if sum of all local counters > global limit → reject
    
    This reduces Redis load by N×, with slight inaccuracy (may allow slightly more than limit)
  
  Nginx rate limiting: ngx_http_limit_req_module (per-server, not distributed)
  AWS API Gateway: built-in rate limiting (per API key)
  Kong / Envoy: distributed rate limiting via Redis
```

---

## Interview Quick Answers

- **What is the difference between token bucket and leaky bucket?** — Token bucket: allows burst up to bucket capacity (tokens accumulate up to max). Leaky bucket: enforces constant output rate regardless of input burst. Token bucket is more common because bursts are acceptable for most APIs. Leaky bucket used when downstream requires constant rate.
- **Why does a sliding window counter use two fixed windows?** — To avoid the boundary attack of a pure fixed window (where a user can double the limit by sending at the end of one window and start of next). The sliding window counter weights the two adjacent windows based on elapsed time, giving a good approximation of a true sliding window with only 2 counters per user.
