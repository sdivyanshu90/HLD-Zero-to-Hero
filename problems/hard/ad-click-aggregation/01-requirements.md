# Step 1 — Requirements

## Functional Requirements

| # | Requirement |
|---|-------------|
| F1 | Count clicks per (ad_id, campaign_id, time_window) |
| F2 | Real-time dashboard: click counts with < 1 min latency |
| F3 | Billing: exact click counts per advertiser per day |
| F4 | Click deduplication (same user, same ad, < 1 hour) |
| F5 | Support filtering: by country, device_type, placement |
| F6 | Handle late-arriving events (up to 1 hour) |
| F7 | Query API: clicks by ad / campaign / time range |

## Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| N1 | Throughput | 10 B clicks/day = 115 K clicks/sec avg; 500 K peak |
| N2 | Dashboard latency | < 60 seconds end-to-end |
| N3 | Billing accuracy | Exact counts (no approximation for money) |
| N4 | Fault tolerance | No event loss; at-least-once processing |
| N5 | Retention | Raw events: 7 days; aggregated: 3 years |

## Key Trade-Off: Dashboard vs Billing

```
Dashboard:
  Needs: low latency (< 1 min)
  Accepts: slight approximation (< 1% error)
  Use: streaming aggregation (Flink tumbling windows)

Billing:
  Needs: exact counts (money!)
  Accepts: higher latency (hourly is fine)
  Use: batch reprocessing of raw events (Spark on S3)
  
→ Lambda Architecture: streaming for speed, batch for accuracy
```
