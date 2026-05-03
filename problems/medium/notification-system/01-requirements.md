# Step 1 — Requirements

## Functional Requirements

| # | Requirement |
|---|-------------|
| F1 | Send push notifications (iOS APNs, Android FCM) |
| F2 | Send email (transactional + marketing) |
| F3 | Send SMS (OTP, alerts) |
| F4 | In-app notifications (bell icon feed) |
| F5 | User preference management (opt-out per channel) |
| F6 | Deduplication (same notification ≤ once per user) |
| F7 | Retry on delivery failure |
| F8 | Notification priority (HIGH: OTP/payment, LOW: marketing) |

## Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| N1 | Throughput | 10 M notifications/day (~115/sec avg, 1000/sec peak) |
| N2 | Latency | HIGH priority < 5s, LOW priority < 60s |
| N3 | Delivery guarantee | At-least-once (idempotent delivery) |
| N4 | High availability | 99.9% uptime |
| N5 | Scalability | Handle 100× spike (product launch) |

## Out of Scope (v1)

- Rich media in push notifications
- A/B testing notification content
- Notification analytics dashboard (v2)
- Scheduled / drip campaigns (v2)
