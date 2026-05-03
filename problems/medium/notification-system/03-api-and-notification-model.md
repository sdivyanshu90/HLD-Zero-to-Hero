# Step 3 — API and Notification Model

## Send Notification API

```
POST /api/v1/notifications
{
  "type": "ORDER_SHIPPED",
  "priority": "HIGH",
  "recipients": [
    {"user_id": "u_12345"}
  ],
  "channels": ["push", "email"],   // null = use user preferences
  "template_id": "order_shipped_v2",
  "template_vars": {
    "order_id": "4521",
    "tracking_url": "https://track.example.com/4521"
  },
  "idempotency_key": "order-4521-shipped-20240503"
}
```

**Response:**
```json
{
  "notification_id": "notif_abc123",
  "status": "QUEUED",
  "estimated_delivery_ms": 3000
}
```

## Notification Data Model

```sql
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         BIGINT NOT NULL,
    type            VARCHAR(64) NOT NULL,
    channel         VARCHAR(16) NOT NULL,  -- push, email, sms, in_app
    status          VARCHAR(16) NOT NULL,  -- queued, sent, failed, deduped
    priority        VARCHAR(8)  NOT NULL,  -- high, normal, low
    idempotency_key VARCHAR(128) UNIQUE,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at         TIMESTAMPTZ,
    error_message   TEXT
);

CREATE INDEX ON notifications(user_id, created_at DESC);
CREATE INDEX ON notifications(status, priority, created_at);
```

## Device Token Storage

```sql
CREATE TABLE device_tokens (
    user_id     BIGINT NOT NULL,
    token       VARCHAR(256) NOT NULL,
    platform    VARCHAR(8) NOT NULL,  -- ios, android
    app_version VARCHAR(16),
    last_seen   TIMESTAMPTZ,
    PRIMARY KEY (user_id, token)
);
```
