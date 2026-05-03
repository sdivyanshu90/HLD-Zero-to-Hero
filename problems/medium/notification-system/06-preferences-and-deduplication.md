# Step 6 — Preferences and Deduplication

## User Preference Schema

```sql
CREATE TABLE notification_preferences (
    user_id     BIGINT NOT NULL,
    notif_type  VARCHAR(64) NOT NULL,   -- ORDER_SHIPPED, PROMO, etc.
    channel     VARCHAR(16) NOT NULL,   -- push, email, sms, in_app
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, notif_type, channel)
);

-- Unsubscribe / global opt-out
CREATE TABLE notification_suppressions (
    user_id     BIGINT NOT NULL,
    channel     VARCHAR(16),   -- null = all channels
    reason      VARCHAR(32),   -- unsubscribe, bounce, complaint, admin
    suppressed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, COALESCE(channel, 'all'))
);
```

## Preference Lookup (Cached)

```python
def is_enabled(user_id: int, notif_type: str, channel: str) -> bool:
    # Check global suppression (cached in Redis, TTL 5min)
    if redis.exists(f"suppressed:{user_id}"):
        return False
    
    # Check per-type preference (DB, cached per session)
    key = f"pref:{user_id}:{notif_type}:{channel}"
    cached = redis.get(key)
    if cached is not None:
        return cached == "1"
    
    result = db.query(
        "SELECT enabled FROM notification_preferences WHERE user_id=? AND notif_type=? AND channel=?",
        user_id, notif_type, channel
    )
    enabled = result.enabled if result else True  # default: enabled
    redis.setex(key, 300, "1" if enabled else "0")
    return enabled
```

## Deduplication

```
Problem: Network retry sends same notification twice

Solution: Idempotency key + Redis NX

On worker:
  key = f"notif_delivered:{idempotency_key}"
  acquired = redis.set(key, "1", nx=True, ex=86400)  # 24h TTL
  if not acquired:
      log("Duplicate notification suppressed")
      return  # already delivered
  
  # proceed with delivery
```

## Suppression List Management

```
On email bounce (hard bounce):
  → add to suppressions (channel=email)
  → never email again

On spam complaint:
  → add to suppressions (channel=email)
  → unsubscribe user

On push token invalid:
  → delete token from device_tokens
  → if no tokens left, can't send push to user

On user opt-out via unsubscribe link:
  → INSERT INTO notification_suppressions
  → clear Redis cache for user preferences
```
