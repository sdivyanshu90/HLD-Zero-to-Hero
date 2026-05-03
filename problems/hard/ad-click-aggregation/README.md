# Ad Click Aggregation — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** Kafka, Flink, streaming, Lambda architecture, deduplication, billing  
**Companies:** Google Ads, Meta Ads, Twitter Ads, Amazon Advertising

---

## Problem Statement

Design a real-time ad click aggregation system that:
- Processes 10 B click events/day from ad networks
- Provides real-time dashboards (< 1 min lag) and exact billing counts
- Deduplicates fraudulent / duplicate clicks
- Handles late events (clicks arriving up to 1 hour late)

---

## Architecture Diagram

```
Ad Click Events (browsers, mobile SDKs)
         │
         ▼
┌────────────────────────┐
│   Kafka Ingestion      │  100K events/sec, 1 KB avg
│   (partitioned by      │
│    campaign_id)        │
└───────────┬────────────┘
            │
    ┌───────┴──────────┐
    ▼                  ▼
┌──────────┐     ┌──────────────────┐
│  Flink   │     │  Batch Reprocess │
│ Streaming│     │  (Spark, hourly) │
│(real-time│     │  exact counts    │
│ approx.) │     └──────────────────┘
└──────────┘           │
    │                  │
    ▼                  ▼
┌─────────────────────────────┐
│   ClickHouse / Druid        │  OLAP store, query in < 1s
│   (serving layer)           │
└─────────────────────────────┘
         │
         ▼
  Advertiser Dashboard + Billing System
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Event Ingest and Throughput](02-event-ingest-and-throughput.md)
3. [Kafka and Partitioning](03-kafka-and-partitioning.md)
4. [Stream Aggregation and Windowing](04-stream-aggregation-and-windowing.md)
5. [Exactness, Deduplication, and Idempotency](05-exactness-deduplication-and-idempotency.md)
6. [Serving Counters and Billing](06-serving-counters-and-billing.md)
7. [Late Events and Reprocessing](07-late-events-and-reprocessing.md)
8. [Checkpoint](08-checkpoint.md)
