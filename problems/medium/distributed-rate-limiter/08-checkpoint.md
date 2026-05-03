# Step 8 — Checkpoint & Interview Q&A

**Q1: What is the boundary attack on fixed-window rate limiting?**
> In a fixed window of 100 req/min, a client can send 100 requests at 23:59:30 (last 30s of window 1) and 100 more at 00:00:01 (first 1s of window 2). In 31 seconds they've sent 200 requests — twice the limit. Sliding window counter mitigates this by weighting the previous window's count.

**Q2: Why use Lua scripts in Redis for rate limiting?**
> Rate limiting requires a read-modify-write cycle (GET counter, check limit, INCR if allowed). Without atomicity, two concurrent threads can both read "99" (under limit) and both increment — allowing 101 requests. Lua scripts execute atomically in Redis's single-threaded interpreter, eliminating this race.

**Q3: Should rate limiter failures cause fail-open or fail-closed?**
> Fail-open for general APIs (brief outage is less harmful than a full service outage). Fail-closed for sensitive endpoints (payments, authentication) where correctness matters more than availability. Implement with a circuit breaker pattern and a short-lived local fallback.

**Q4: How do you rate-limit across multiple servers sharing a global quota?**
> Use centralised Redis as the shared counter store. Each server's rate limit middleware calls Redis with a Lua script on every request. The 2-5ms Redis overhead is acceptable. For higher throughput, use a local counter that syncs with Redis every 100ms (local-first, periodic sync pattern).

**Q5: How do you handle per-user rate limits for 100 M users?**
> Each user gets a Redis key only when they make a request. Keys auto-expire (TTL = window size × 2). At any point only actively-requesting users have keys in Redis. With 100K active users × 3 windows × 100B = 30 MB — trivially small.

## Interview Checklist

- [ ] Can explain all 5 algorithm trade-offs
- [ ] Can write token bucket logic in pseudocode
- [ ] Can explain why Lua is needed in Redis
- [ ] Know fail-open vs fail-closed scenarios
- [ ] Can describe multi-region challenges
