# Step 4 — Token Bucket and Other Algorithms

## Algorithm Comparison

| Algorithm | Pros | Cons | Best For |
|-----------|------|------|---------|
| Token Bucket | Allows bursts; smooth refill | State per key | API quotas with burst |
| Leaky Bucket | Smooth output rate | No burst allowed | Video streaming |
| Fixed Window Counter | Simple, low memory | Boundary attack (2× burst) | Simple quotas |
| Sliding Window Log | Accurate | High memory (log per request) | Accurate tracking |
| Sliding Window Counter | Good accuracy, low memory | Approximate (weighted) | Production default |

## Fixed Window Counter — Boundary Attack

```
Limit: 100 req/min

Window 1: 23:59:00 → 00:00:00  →  100 requests (at 23:59:30)
Window 2: 00:00:00 → 00:01:00  →  100 requests (at 00:00:01)

From 23:59:30 to 00:00:01 (30 seconds): 200 requests!
→ 2× the intended limit
```

## Sliding Window Counter (Cloudflare Approach)

```
current_count = requests[current_window]
               + requests[prev_window] × (window_size - elapsed) / window_size

Example (per-minute, limit=100):
  current minute (40s elapsed): 45 requests
  previous minute: 72 requests

  overlap_weight = (60 - 40) / 60 = 0.333
  weighted_prev  = 72 × 0.333    = 23.98
  total          = 45 + 23.98    = 68.98  < 100  → allow
```

## Token Bucket State

```
State per key:
  tokens:         current token count (float)
  last_refill_ts: unix timestamp of last refill

Refill logic (lazy):
  elapsed = now - last_refill_ts
  new_tokens = elapsed × (limit / window)
  tokens = min(capacity, tokens + new_tokens)

Check:
  if tokens >= 1:
    tokens -= 1; return ALLOW
  else:
    return DENY; retry_after = (1 - tokens) / refill_rate
```

## Visual: Token Bucket

```
capacity = 10 tokens
refill   = 1 token/sec

t=0:  [██████████]  10 tokens
burst of 8 requests:
t=0:  [██        ]   2 tokens
t=3s: [█████     ]   5 tokens (refilled +3)
t=8s: [██████████]  10 tokens (full)
```
