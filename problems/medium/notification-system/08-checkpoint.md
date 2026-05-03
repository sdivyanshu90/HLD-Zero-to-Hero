# Step 8 — Checkpoint & Interview Q&A

**Q1: How do you prevent sending the same notification twice?**
> Each notification has an `idempotency_key` (e.g., `order-4521-shipped`). Before delivery, the worker does `SET notif_delivered:{key} 1 NX EX 86400` in Redis. If the key already exists (NX returns nil), the message is a duplicate and is skipped. This handles Kafka at-least-once redelivery on worker restart.

**Q2: How do you handle user opt-out/preferences at high scale?**
> Preferences are stored in a relational DB and cached in Redis per-user with a 5-minute TTL. Suppressions (hard bounces, global opt-outs) are cached indefinitely and only invalidated when updated. At 100K req/sec, Redis absorbs all preference lookups.

**Q3: What happens when a push notification provider (APNs) is down?**
> Workers retry with exponential backoff (5 attempts). HIGH priority notifications fail quickly and trigger an in-app notification fallback. After max retries, the message goes to the Dead Letter Queue where ops can investigate and re-process when APNs recovers.

**Q4: How do you handle a mass notification to 50 M users (product launch)?**
> Write to Kafka in batches (producer batching). Fan-out workers read in parallel from many partitions. Email workers batch 1000 personalizations per SendGrid call. Throttle to respect provider rate limits. Total delivery time: ~50 M / 100 workers × 1 ms/send ≈ 500 seconds ≈ 8 minutes (acceptable for marketing).

**Q5: How do you ensure HIGH priority notifications (OTPs) always go through?**
> Separate Kafka topic with higher consumer group count. Skip user preference check for CRITICAL type notifications. Multiple provider fallbacks (Twilio primary → AWS SNS fallback). Dedicated Redis instances for dedup (no memory contention with low-priority notifications). SLA monitoring with alerting if delivery > 5s.
