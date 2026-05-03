# Notification System — System Design Walkthrough

**Difficulty:** Medium  
**Tags:** async, Kafka, push, email, SMS, fan-out, deduplication  
**Companies:** Facebook, Airbnb, Uber, LinkedIn

---

## Problem Statement

Design a notification system that:
- Sends push, email, SMS, and in-app notifications
- Handles 10 M+ notifications/day with < 5s delivery latency
- Supports user preferences (opt-out, channel selection)
- Deduplicates notifications and retries on failure

---

## Architecture Diagram

```
Event Sources (Order, Payment, Social)
         │
         ▼
┌────────────────────────┐
│   Notification Service │  creates notification job
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     Kafka Topics       │  priority queues
│  high_priority         │  (payment alerts)
│  normal_priority       │  (social, marketing)
└───────────┬────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌────────┐   ┌──────────┐
│ Push   │   │  Email   │
│Workers │   │ Workers  │  ... (SMS, In-App)
└────────┘   └──────────┘
     │             │
  APNs/FCM       SendGrid/SES
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic and Fan-Out Model](02-traffic-and-fan-out-model.md)
3. [API and Notification Model](03-api-and-notification-model.md)
4. [Queueing and Worker Pipeline](04-queueing-and-worker-pipeline.md)
5. [Channel Providers and Delivery](05-channel-providers-and-delivery.md)
6. [Preferences and Deduplication](06-preferences-and-deduplication.md)
7. [Retries, Rate Limits, and Failures](07-retries-rate-limits-and-failures.md)
8. [Checkpoint](08-checkpoint.md)
