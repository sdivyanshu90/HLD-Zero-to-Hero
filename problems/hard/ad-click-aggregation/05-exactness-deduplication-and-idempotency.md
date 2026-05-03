# Step 5 — Exactness, Deduplication, and Idempotency

## Click Deduplication Problem

```
Sources of duplicate clicks:
  1. User double-clicks the ad (same ad, same user, < 1 sec)
  2. Browser retry on network timeout (same click_id)
  3. Kafka at-least-once redelivery (Flink worker restarts)
  4. Bot / click fraud (same user_id / IP clicks 100× in 1 min)
```

## Dedup Layer 1: Client-Side

```
Browser / mobile SDK:
  Generate unique click_id (UUID v4) on first click
  Mark as "submitted"; suppress re-sends for 30 seconds
  Include click_id in event payload
```

## Dedup Layer 2: Redis NX at Ingest

```python
def ingest_click(click_event: ClickEvent) -> bool:
    dedup_key = f"click:{click_event.click_id}"
    
    # SET NX EX 3600 (1-hour dedup window)
    if not redis.set(dedup_key, "1", nx=True, ex=3600):
        metrics.increment("duplicate_click_suppressed")
        return False  # duplicate
    
    kafka.produce("ad-clicks-raw", click_event.to_json())
    return True
```

**Memory:** 1 B clicks/day × 36 bytes per Redis key = 36 GB  
→ Use Redis Cluster with 4 nodes × 16 GB RAM

## Dedup Layer 3: Bloom Filter (for fraud detection)

```
For detecting click fraud (same IP, 100 clicks/min):
  Sliding window count per (user_id, ad_id, 1-hour bucket)
  
Redis:
  INCR click_count:{user_id}:{ad_id}:{hour}
  EXPIRE key 7200 (2 hours)
  if count > 10: flag as fraud, don't count
```

## Exactly-Once in Flink

```
Flink exactly-once semantics with Kafka:
  1. Kafka source: committed offsets only on checkpoint success
  2. Flink checkpoints: state snapshot saved to S3
  3. Kafka sink: transactional producer
     - 2-phase commit: pre-commit on checkpoint, commit on complete
  4. On failure: restore from last checkpoint, replay from committed offset

Result: exactly-once end-to-end for streaming aggregation
```

## Billing: Batch Reprocessing for Exactness

```
Even with streaming dedup, streaming counts can have edge cases:
  - Flink window state lost during major failure
  - Late events arrive after window close

For billing, always use batch:
  1. S3 Parquet files: raw events, immutable, deduplicated
  2. Spark job runs hourly: COUNT DISTINCT click_id per ad per day
  3. Results written to billing_counts table
  4. Reconcile with streaming counts; alert if diff > 1%
```
