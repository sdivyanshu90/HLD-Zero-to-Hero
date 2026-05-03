# Step 5 — Channel Providers and Delivery

## Push Notifications (APNs / FCM)

```
iOS (APNs):
  Token-based auth (JWT, p8 file)
  HTTP/2 connection to api.push.apple.com:443
  Max payload: 4 KB
  Response codes:
    200 → success
    400 BadDeviceToken → delete token from DB
    410 Unregistered  → delete token from DB
    429 TooManyRequests → backoff + retry

Android (FCM):
  Firebase Admin SDK or REST API
  HTTP POST https://fcm.googleapis.com/v1/projects/{id}/messages:send
  Max payload: 4 KB (data), 1 KB (notification)
  Handles iOS too (unified API via Firebase)
```

## Email (SendGrid / SES)

```
SendGrid:
  POST /v3/mail/send
  Bulk personalizations (up to 1000 recipients per request)
  Rate limit: 600 req/min on free, custom on paid plans
  Bounce/spam webhooks → update suppression list

Amazon SES:
  14 req/sec (default), scalable with approval
  Integrated with IAM, cheaper at scale
  SNS notifications for bounces/complaints
```

## SMS (Twilio / SNS)

```
Twilio:
  POST /2010-04-01/Accounts/{sid}/Messages.json
  Rate: 1 message/sec per number (US)
  Use messaging pools or short codes for volume

Reliability considerations:
  - Carrier filtering (spam detection)
  - Country-specific regulations (GDPR, TCPA)
  - Delivery receipts are unreliable
  → always have email as fallback for critical OTPs
```

## Provider Abstraction Layer

```python
class NotificationProvider(ABC):
    @abstractmethod
    def send(self, recipient: str, payload: dict) -> DeliveryResult: ...

class APNsProvider(NotificationProvider): ...
class FCMProvider(NotificationProvider): ...
class SendGridProvider(NotificationProvider): ...
class TwilioProvider(NotificationProvider): ...

# Factory with fallback
class ProviderFactory:
    def get_providers(self, channel: str) -> List[NotificationProvider]:
        if channel == "push":
            return [APNsProvider(), FCMProvider()]
        elif channel == "email":
            return [SendGridProvider(primary=True), SESProvider(fallback=True)]
        elif channel == "sms":
            return [TwilioProvider(), SNSProvider()]
```
