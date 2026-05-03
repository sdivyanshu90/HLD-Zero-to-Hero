# Twitter Newsfeed — System Design Walkthrough

**Difficulty:** Medium  
**Tags:** fan-out, Redis ZSET, hybrid, celebrity problem, timeline  
**Companies:** Twitter, Instagram, LinkedIn, Weibo

---

## Problem Statement

Design Twitter's newsfeed (home timeline) that:
- Shows the latest tweets from accounts a user follows
- Handles 300 M DAU with 100 M tweets/day
- Delivers feed loads in < 200 ms
- Handles celebrities with 10 M+ followers efficiently

---

## Architecture Diagram

```
User posts tweet
      │
      ▼
┌─────────────┐     ┌──────────────────────────────────┐
│ Tweet Svc   │────►│  Fan-Out Service                  │
└─────────────┘     │  (fan-out-on-write OR lazy)       │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
             ┌────────────┐ ┌──────────┐ ┌────────────┐
             │ User A's   │ │ User B's │ │ User C's   │
             │ Feed ZSET  │ │ Feed ZSET│ │ Feed ZSET  │
             │ (Redis)    │ │ (Redis)  │ │ (Redis)    │
             └────────────┘ └──────────┘ └────────────┘
                    │
                    ▼
         ┌────────────────────┐
         │   Tweet DB         │  stores actual tweet content
         │  (Cassandra/MySQL) │
         └────────────────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic and Data Shape](02-traffic-and-data-shape.md)
3. [API Design](03-api-design.md)
4. [Feed Write and Read Models](04-feed-write-and-read-models.md)
5. [Hybrid Fan-Out Strategy](05-hybrid-fan-out-strategy.md)
6. [Timeline Caching](06-timeline-caching.md)
7. [Failure Modes and Trade-Offs](07-failure-modes-and-trade-offs.md)
8. [Checkpoint](08-checkpoint.md)
