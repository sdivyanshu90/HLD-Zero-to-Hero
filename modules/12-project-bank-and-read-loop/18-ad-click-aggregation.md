# Cheat Sheet: Ad Click Aggregation

## Scale (BoE)
```
Ad impressions per day: 10B (Google AdWords scale)
Click-through rate: ~0.1% → 10M clicks/day
Click event QPS: 10M / 86,400 ≈ 115 clicks/second average
Peak: 500 clicks/second (during high-traffic events)
Billing: must accurately aggregate clicks per ad per billing period
Latency: near-real-time aggregate (< 1 minute delay for monitoring)
```

## System Diagram
```
Browser ──click event──▶ Click Tracker API ──▶ Kafka (click_events topic)
                              │                        │
                         Validate,                Stream Processor
                         filter bots              (Flink/Spark Streaming)
                                                        │
                                              ┌─────────┴─────────┐
                                              ▼                    ▼
                                     Near-real-time           Batch (hourly)
                                     aggregation              reconciliation
                                     (per-minute window)      (exact count)
                                              │
                                       Results DB (Cassandra)
                                       ad_id, window, click_count
                                              │
                                       Billing Service reads
                                       Advertiser dashboard reads
```

## Stream Aggregation with Windowing

```
Kafka: click_events topic, partitioned by ad_id
  Each Flink consumer group reads assigned partitions

Flink tumbling window (1-minute window):
  Window [12:00:00 - 12:00:59]: count clicks per ad_id
  Window closes at 12:01:00 → emit aggregated counts
  → Write: (ad_id=123, window=12:00, count=450) to Cassandra
  
  Sliding window (for fraud detection):
    1-minute window sliding every 10 seconds
    Alert if clicks > 10× baseline in any 1-minute window

Late event handling:
  Flink watermarks: wait up to 30 seconds for late events
  If event arrives after watermark: goes to side-output (late data)
  Reprocess late data in batch reconciliation
```

## Deduplication (Exactly-Once Counting)

```
Problem: user clicks same ad 3 times in 1 second (accidental triple-click)
  → Count as 1 unique click for billing

Dedup strategies:
  1. Client-side: disable button after first click (UX fix)
  2. Session dedup: hash(user_id + ad_id + session_id) → count once per session
  3. Time window dedup: same user + same ad in last 60 seconds = deduplicate
  
  Implementation:
    Redis SET: "seen:{user_id}:{ad_id}" NX EX 60  (60 second window)
    If SET returns 0: duplicate → skip
    If SET returns 1: first click → count it
```

## Billing Accuracy

```
Near-real-time (Flink, 1-min windows) → dashboard, monitoring
Batch (Spark hourly job) → exact count from Kafka log → billing truth

Two-layer architecture:
  Layer 1: Streaming (fast, approximate, for UI/monitoring)
  Layer 2: Batch (slower, exact, for billing/SLA)
  
  Kafka: retain click events for 7 days
  If discrepancy found: reprocess from Kafka log (replay)
  Advertiser billing: always from batch counts (source of truth)
```

## Unique Trick
Lambda Architecture: run both a streaming layer (fast, approximate, serves live queries) and a batch layer (slow, exact, serves historical/billing). The batch layer periodically "corrects" the streaming layer's approximations. Kafka as the durable log makes the batch layer possible (can replay from any offset).
