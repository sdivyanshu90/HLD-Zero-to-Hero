# Problems

Structured HLD problem walkthroughs organized by difficulty.

---

## Easy

| Project | Description |
|---------|-------------|
| [URL Shortener](easy/url-shortener/README.md) | Design a TinyURL-style URL shortening service |
| [Distributed Cache](easy/distributed-cache/README.md) | Design a Redis-like distributed in-memory cache |
| [Distributed ID Generator](easy/distributed-id-generator/README.md) | Design a Snowflake-style unique ID generator |

---

## Medium

| Project | Description |
|---------|-------------|
| [Distributed Rate Limiter](medium/distributed-rate-limiter/README.md) | Token bucket / sliding window rate limiting |
| [Notification System](medium/notification-system/README.md) | Multi-channel push/email/SMS notifications |
| [Realtime Chat System](medium/realtime-chat-system/README.md) | WebSocket-based chat (Slack/WhatsApp-style) |
| [Ticket Booking System](medium/ticket-booking-system/README.md) | Seat reservation with concurrency control |
| [Twitter Newsfeed](medium/twitter-newsfeed/README.md) | Fan-out write/read, timeline caching |

---

## Hard

| Project | Description |
|---------|-------------|
| [Ad Click Aggregation](hard/ad-click-aggregation/README.md) | Real-time click counting with Kafka + stream processing |
| [Collaborative Text Editor](hard/collaborative-text-editor/README.md) | OT/CRDT-based realtime collaborative editing |
| [Distributed File Storage](hard/distributed-file-storage/README.md) | Dropbox-style chunked file sync and dedup |
| [Distributed Web Crawler](hard/distributed-web-crawler/README.md) | Polite, deduplicated web crawler at web scale |
| [Food Delivery Platform](hard/food-delivery-platform/README.md) | DoorDash-style order lifecycle and dispatch |
| [Metrics Monitoring & Alerting](hard/metrics-monitoring-and-alerting/README.md) | Datadog-style TSDB, dashboards, and alerts |
| [Payment Ledger Platform](hard/payment-ledger-platform/README.md) | Double-entry bookkeeping with idempotency |
| [Realtime Multiplayer Game Backend](hard/realtime-multiplayer-game-backend/README.md) | UDP game state sync, lag compensation |
| [Search Autocomplete](hard/search-autocomplete/README.md) | Trie-based prefix suggestions at Google scale |
| [Service Discovery & Config](hard/service-discovery-and-config/README.md) | Consul/etcd-style registry and config push |
| [Uber Ride Sharing](hard/uber-ride-sharing/README.md) | Geospatial matching, surge pricing, driver routing |
| [Video Streaming Platform](hard/video-streaming-platform/README.md) | Netflix-style transcoding, CDN, and adaptive bitrate |

---

## Format

Each problem follows the same structure:
```
problems/{difficulty}/{project}/
    README.md              — problem statement, architecture diagram, study order
    01-requirements.md     — functional + non-functional requirements
    02-...                 — traffic, capacity, data model
    ...
    08-checkpoint.md       — interview Q&A with deep-dive answers
```

See [solutions/](../solutions/README.md) for Python implementations.
