# Step 4 — Queueing and Worker Pipeline

## Pipeline Architecture

```
1. Notification Service receives request
2. Validates + enriches (fetch user preferences, device tokens)
3. Publishes to Kafka topic based on priority
4. Channel Workers consume from Kafka
5. Workers call external providers (APNs, FCM, SendGrid)
6. Workers update notification status in DB
7. Failed deliveries → Dead Letter Topic (DLT) for retry

┌─────────────────────────────────────────────────────────┐
│                     Kafka                               │
│  ┌──────────────────┐  ┌──────────────────────────────┐│
│  │ high_priority    │  │ normal_priority               ││
│  │ (push + SMS OTP) │  │ (email + marketing push)      ││
│  └────────┬─────────┘  └──────────────┬───────────────┘│
└───────────┼───────────────────────────┼─────────────────┘
            │                           │
   ┌────────▼──────┐          ┌─────────▼──────┐
   │ Push Workers  │          │ Email Workers  │
   │ (consume fast)│          │ (bulk batching)│
   └───────────────┘          └────────────────┘
```

## Worker Design

```python
class PushNotificationWorker:
    def process(self, message: KafkaMessage):
        notif = NotificationJob.from_json(message.value)
        
        # 1. Dedup check
        if self.redis.set(
            f"notif_sent:{notif.idempotency_key}",
            "1", nx=True, ex=86400
        ) is None:
            return  # already sent
        
        # 2. Fetch device tokens
        tokens = self.db.get_device_tokens(notif.user_id)
        
        # 3. Check user preferences
        if not self.prefs.is_channel_enabled(notif.user_id, "push"):
            return  # user opted out
        
        # 4. Send via provider
        for token in tokens:
            try:
                self.apns.send(token, notif.payload)
                self.db.mark_sent(notif.id)
            except InvalidTokenError:
                self.db.delete_device_token(token)
            except ProviderError as e:
                self.db.mark_failed(notif.id, str(e))
                raise  # re-raise for Kafka retry
```

## Batching for Email Workers

```
Email providers (SendGrid, SES) have per-second API rate limits.
Batch emails to reduce API calls:
  - Consumer groups batch 100 notifications
  - Single API call: POST /v3/mail/send with 100 personalizations
  - Reduces 100 API calls to 1
```
