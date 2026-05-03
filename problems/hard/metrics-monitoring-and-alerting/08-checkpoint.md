# Step 8 — Checkpoint & Interview Q&A

**Q1: What is cardinality and why is it a challenge in metrics systems?**
> Cardinality = number of unique time series = product of unique values per label. `http_requests{service="*", endpoint="*", status="*"}` with 100 services × 1000 endpoints × 10 statuses = 1 M time series. High cardinality explodes memory (each series needs state for aggregation) and query time. Mitigation: limit label values (no UUIDs as labels), drop high-cardinality labels at ingestion.

**Q2: How does downsampling work?**
> High-resolution data (1s interval) is retained for 7-15 days. Downsampling workers aggregate: every 5 min, compute min/max/avg/p99 over the last 5 min and write as a single data point. Downsampled tiers: 1s (15d), 1m (3 months), 1h (2 years). Queries automatically use the coarsest available resolution that satisfies the time range and group-by interval.

**Q3: How do you ensure alerts fire within 60 seconds?**
> Alert rules run as Prometheus queries every 15 seconds. On threshold breach, send FIRING event to Alertmanager. Alertmanager deduplicates (same alert from multiple replicas), groups related alerts, and routes to PagerDuty/Slack. End-to-end: metric collected (0-15s) → alert evaluated (0-15s) → notification sent (5-10s) = worst case ~40s, typically < 30s.

**Q4: How do you store 100K metrics/sec at 1-second resolution cost-effectively?**
> Local Prometheus scrapes and compresses (delta-of-delta + Gorilla XOR encoding): ~1.3 bytes per sample. 100K × 86400 × 1.3 bytes = ~10 GB/day. For 15 days = 150 GB (Prometheus). For long-term at scale: Thanos or Cortex compacts and stores in S3 (Parquet blocks). 1 year of 1-minute data for 100K series ≈ 100 GB on S3 ($2.30/month).

**Q5: How do you handle a monitoring system failure without losing metrics?**
> Agents buffer locally: each service agent (Vector, Datadog agent) buffers metrics to disk (up to 1 GB) and retries sending on reconnect. Kafka: ingestion pipeline backed by Kafka (replay on failure). Prometheus federation: secondary Prometheus instances can be promoted. Alert on monitoring system health itself (meta-monitoring).
