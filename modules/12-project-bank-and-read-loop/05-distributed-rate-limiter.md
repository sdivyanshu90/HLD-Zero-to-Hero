# Cheat Sheet: Distributed Rate Limiter

## Scale (BoE)
```
APIs to rate limit: 1000 different endpoints
Users: 10M users
Target: 100 req/min per user per endpoint
Peak rate check QPS: 10M users × 10 API calls/min / 60 = ~1.7M checks/second
```

## System Diagram
```
Client ──request──▶ API Gateway ──rate_check──▶ Redis
                        │                      (token bucket or
                        │ deny (429)            sliding window counter)
                        ▼
                    Service

Redis key: "rate:{user_id}:{endpoint}:{window_minute}"
Redis command: INCR rate:1234:POST_orders:202312101400
               EXPIRE rate:1234:POST_orders:202312101400 60
If count > limit → 429 Too Many Requests
```

## Algorithm Comparison
```
Token bucket:
  Redis hash: {tokens: 95, last_refill: 1703120000}
  On each request: tokens -= 1; if tokens < 0: reject
  Background: refill at rate R/second up to capacity C
  ✓ Handles burst (can use accumulated tokens)

Sliding window counter (recommended for distributed):
  Two Redis INCR keys (current + previous minute)
  Weighted estimate: prev × (1 - elapsed) + curr
  ✓ No boundary attack, memory efficient, O(1) Redis ops
  ✓ Used by Stripe, Cloudflare
```

## Key Design Decisions

**1. Granularity:**
- Per-user + per-endpoint: most granular but more Redis keys
- Per-user only: simpler, allows users to spam one endpoint
- Per-IP: handles unauthenticated endpoints

**2. Distributed consistency:**
- Redis INCR is atomic → safe for concurrent servers
- For very high throughput: local counter per app server, sync to Redis every 100ms
  (allows slightly over limit but reduces Redis load by N×)

**3. Response headers:**
- Always return: `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 45`, `X-RateLimit-Reset: 1703120060`

## Bottlenecks
1. Redis latency: ~0.5ms per rate check → for 1M QPS: 500 Redis QPS × N endpoints → Redis cluster needed
2. Fairness: per-IP rate limiting can affect users behind NAT (many users share one IP)

## Unique Trick
For rate limiting at the CDN/DDoS layer, use Cloudflare Rate Limiting rules (processed at edge, before traffic hits your origin). For API-level rate limiting, Redis sliding window counter with Lua scripts for atomic multi-key operations.
