# Step 8 — Checkpoint & Interview Q&A

**Q1: Why is Lambda Architecture used here instead of pure streaming?**
> Streaming (Flink) provides low latency but can have edge cases in exactness (window state loss, late events). Billing requires exact counts — money is involved. Lambda uses streaming for real-time dashboards (speed layer) and batch (Spark on S3) for exact billing counts (batch layer). The batch layer overwrites streaming results daily.

**Q2: How do you deduplicate 10 B clicks/day?**
> Three-layer dedup: (1) Client-side: generate unique click_id, suppress retries for 30s. (2) Ingest layer: Redis SET NX EX 3600 — only one click per click_id per hour reaches Kafka. (3) Batch: exact dedup in Spark using COUNT DISTINCT click_id for billing. The Redis layer handles ~99.9% of duplicates; batch catches the rest.

**Q3: How do late-arriving events affect your aggregation?**
> Flink watermarks allow events up to 1 minute late. After the window fires, events in a side-output "late data" stream are collected and used to correct counts via incremental updates to ClickHouse. For billing (daily totals), the batch job at T+1 hour processes all events for the day including all late arrivals.

**Q4: How would you detect click fraud in real-time?**
> Count clicks per (user_id, ad_id) in a 1-hour sliding window using Redis INCR with TTL. Flag if count > threshold (e.g., 10 clicks/hour). Enrich events with IP, user-agent, geolocation. Apply ML model (XGBoost) on feature vectors: click velocity, IP reputation, device fingerprint. Fraudulent clicks are filtered before aggregation.

**Q5: How do you ensure ClickHouse doesn't get overwhelmed by Flink outputs?**
> Batch ClickHouse writes: Flink sink buffers 10,000 rows or 5 seconds and inserts as a bulk batch. ClickHouse INSERT performance: 100K rows/sec per node. With 200 partitions of Flink outputting 60 aggregates/partition/min = 12K rows/min = trivial for ClickHouse. For high-cardinality ad clicks, use ReplacingMergeTree to handle late updates.
