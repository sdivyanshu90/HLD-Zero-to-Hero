# Cheat Sheet: Notification System

## Scale (BoE)
```
Users: 1B registered users
Notifications per day: 10B (social, marketing, transactional)
Average QPS: 10B / 86,400 ≈ 115K notifications/second
Notification types: Push (iOS/Android), Email, SMS
Channels: 60% push, 30% email, 10% SMS
Push QPS: 115K × 60% = 69K push/second
```

## System Diagram
```
Event Source ──▶ Notification Service ──▶ [Fan-out Workers]
  (order placed,      │                         │
   comment liked,     │                   ┌─────┼──────┐
   etc.)              │                   ▼     ▼      ▼
                      │              iOS/FCM  Email   SMS
                      │              (APNs)  (SES)   (Twilio)
                      │
                 Priority Queue
                 (HIGH: transactional, security alerts)
                 (LOW: marketing, social)
                      │
                 User Preference Service
                 (check: user opted in? quiet hours?)
```

## Key Design Decisions

**1. Fan-out:**
- One event triggers notifications to many users (new post → notify all followers)
- Use Kafka topics per notification type (high volume, async processing)
- Fan-out workers per channel (push, email, SMS in separate queues)

**2. Deduplication:**
- Same notification sent twice (e.g., retry) → idempotency_key per notification
- Redis SET NX: "notif:{notif_id}" NX EX 86400 → reject duplicate delivery

**3. User preferences:**
- Frequency: don't send >N notifications/day to same user
- Quiet hours: no notifications between 10 PM - 8 AM user's local time
- Opt-out: per-channel opt-out (no email but allow push)
- Rate limit per user per notification type

**4. Delivery tracking:**
- Push: delivery receipt from APNs/FCM (delivered, failed, device not registered)
- Email: bounce/open tracking via SendGrid webhooks
- SMS: delivery receipt from Twilio

## Bottlenecks
1. SMS cost: at $0.01/SMS × 1B = $10M/day at scale → aggressive batching and opt-in only
2. Push token management: devices change tokens on reinstall → stale tokens cause failures

## Unique Trick
Priority queues: transactional notifications (password reset, order confirmation, security alert) must be delivered instantly and reliably. Marketing/social notifications are low priority. Use separate Kafka topics/consumer groups or RabbitMQ queues with different priorities and consumer SLAs.
