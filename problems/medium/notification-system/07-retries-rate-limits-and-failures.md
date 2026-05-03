# Step 7 — Retries, Rate Limits, and Failures

## Retry Strategy

```
Exponential backoff with jitter:
  attempt 1: wait 1s  + jitter(0-0.5s)
  attempt 2: wait 2s  + jitter
  attempt 3: wait 4s  + jitter
  attempt 4: wait 8s  + jitter
  attempt 5: dead letter queue (DLT)

Max retries by priority:
  HIGH (OTP): 5 retries over 30s
  NORMAL:     3 retries over 5 min
  LOW:        2 retries over 1 hour
```

## Dead Letter Queue Processing

```
After max retries, message moves to DLT:
  - Operations team alerted
  - Manual review possible
  - Automated report: "delivery failed, user not notified"

DLT consumers run on schedule (e.g., every 30 min):
  - Re-attempt delivery if provider is now available
  - Mark as permanently failed if user token invalid
```

## Provider Rate Limit Handling

```
FCM rate limit hit:
  1. Catch 429 response
  2. Read Retry-After header
  3. Put token back in queue with delay
  4. Use token bucket locally (pre-emptive rate limiting)

SendGrid rate limit:
  1. Reduce concurrency of email workers
  2. Use SendGrid subuser accounts to multiply rate limits
  3. Implement request queuing per account
```

## Failure Scenarios

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Kafka partition down | Notifications queued, delivered after recovery | Kafka replication factor 3 |
| Redis (dedup) down | May send duplicates | Fail open; idempotent providers handle gracefully |
| APNs unreachable | Push notifications delayed | Retry queue; fallback to in-app |
| SendGrid outage | Emails delayed | Switch to SES fallback provider |
| DB write fails (mark sent) | Notification sent but status wrong | Kafka consumer retries → dedup prevents re-send |
| Worker OOM crash | Kafka offset not committed | Kafka re-delivers from last committed offset |
