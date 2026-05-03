# Step 1 — Requirements

## Functional Requirements

| # | Requirement | Example |
|---|-------------|---------|
| F1 | Per-user rate limit | 100 req/min per user_id |
| F2 | Per-IP rate limit | 1000 req/min per IP |
| F3 | Per-API-key rate limit | 10 K req/hour per API key |
| F4 | Multiple granularities | second / minute / hour / day |
| F5 | Return limit headers | `X-RateLimit-Remaining`, `Retry-After` |
| F6 | Graceful degradation | Allow traffic if rate limiter is down |

## Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| N1 | Latency overhead | < 5 ms per check (p99) |
| N2 | Throughput | 100 K req/sec cluster-wide |
| N3 | Consistency | Soft limits (over by < 5%) acceptable |
| N4 | High availability | Rate limiter failure → fail open |
| N5 | Accuracy | No under-counting on critical payment APIs |

## Limit Key Hierarchy

```
Most specific wins (first match):
  1. user_id:endpoint         (e.g., payment API: 10 req/min)
  2. user_id                  (e.g., 1000 req/hour total)
  3. api_key                  (e.g., 50K req/day)
  4. ip_address               (anti-abuse: 10K req/hour)
  5. global endpoint limit    (e.g., /login: 100K req/min)
```
