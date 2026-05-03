# Step 3 — API Surface and Limit Keys

## Rate Limiter Interface

```python
class RateLimiter:
    def check_and_increment(
        self,
        key: str,           # e.g., "user:12345"
        limit: int,         # max requests
        window_seconds: int # window size
    ) -> RateLimitResult:
        ...

@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_at: int     # unix timestamp
    retry_after: int  # seconds (0 if allowed)
```

## Key Design

```
Key format: rl:{type}:{identifier}:{granularity}:{window_id}

Examples:
  rl:user:u_12345:min:20240503-1030   → user per-minute
  rl:ip:192.168.1.1:min:20240503-1030 → IP per-minute
  rl:apikey:ak_abcdef:hour:20240503-10 → API key per-hour

Window ID derivation:
  Per-second:  window_id = floor(ts / 1)
  Per-minute:  window_id = floor(ts / 60)
  Per-hour:    window_id = floor(ts / 3600)
```

## Configuration Store

```yaml
# rate_limits.yaml
- key_pattern: "user:*"
  limit: 1000
  window: 60s
  
- key_pattern: "user:*:POST:/api/payments"
  limit: 10
  window: 60s
  
- key_pattern: "ip:*"
  limit: 500
  window: 60s
  
- key_pattern: "global:/api/login"
  limit: 100000
  window: 60s
```
