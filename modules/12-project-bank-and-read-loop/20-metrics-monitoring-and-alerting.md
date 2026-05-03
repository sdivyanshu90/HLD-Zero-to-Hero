# Cheat Sheet: Metrics Monitoring and Alerting

## Scale (BoE)
```
Hosts monitored: 10,000 servers
Metrics per host: 100 (CPU, memory, disk, network, custom app metrics)
Collection interval: 10 seconds
Total metrics/second: 10,000 × 100 / 10 = 100,000 metrics/second (100K metrics/s)
Metric data point size: ~50 bytes (timestamp + value + labels)
Write throughput: 100K × 50 bytes = 5 MB/s
Storage for 1 year: 5 MB/s × 86,400 × 365 = ~158 TB (before compression, ~10× compressible = 15 TB)
```

## Time Series Database

```
Time-series data:
  {metric: "cpu.usage", host: "web-01", value: 72.3, timestamp: 1703120000}
  
  Access patterns:
    Write: very high (100K/s), always recent timestamps (append-heavy)
    Read: range queries over time (last 1 hour, last 7 days)
    No random point lookups by timestamp
    Old data less valuable: downsample after 30 days (1h resolution instead of 10s)
  
  Purpose-built TSDBs (vs relational):
    Prometheus: pull-based, local storage, 15 seconds scrape
    InfluxDB: push-based, SQL-like query, tag-based indexing
    TimescaleDB: PostgreSQL extension, SQL-native, hypertable partitioning
    Cassandra: wide-column, partitioned by metric+bucket, manual time-series
    Thanos/Cortex: Prometheus + object storage (S3) for long-term retention
```

## System Diagram
```
Service ──push metrics──▶ StatsD / Prometheus exporter
                              │
                         Kafka (metrics topic, 100K metrics/s)
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
               Time Series DB        Alert Engine
               (InfluxDB/Thanos)     (evaluate rules every 30s)
                    │                    │
               Grafana (dashboards)  Alert Manager
                                     (deduplicate, route, silence)
                                          │
                                    PagerDuty / Slack / Email
```

## Alerting Rules

```
Simple threshold:
  ALERT: cpu.usage > 90% for 5 minutes
  → Fire: CPU high on web-01

Anomaly detection:
  ALERT: metric > (mean + 3×stddev) over last 1 hour
  → Fire: unusual spike above historical baseline

Alert deduplication:
  Alert engine fires alert every 30s while condition met
  Alert Manager deduplicates: only page once per 1-hour window
  Grouping: multiple hosts with same alert → single grouped notification
  Routing: database alerts → DB on-call; web alerts → web on-call

Silence: acknowledge alert for 4 hours during planned maintenance
```

## Data Downsampling

```
Hot data (last 24h): 10-second resolution (full precision)
Warm data (1d-30d): 1-minute resolution (downsample: average over 6 points)
Cold data (30d-1yr): 1-hour resolution
Archive (1yr+): 1-day resolution or delete

Why: 1 year at 10s = 3.1M data points per metric × 1M metrics = 3 quadrillion points
After downsampling: 87K points per metric (1-hour resolution) → 1000× compression
```

## Unique Trick
Prometheus uses a pull model: it scrapes each service's /metrics endpoint every 15 seconds. This means: services don't need to know about Prometheus, configuration is in Prometheus (not in services), and it automatically detects when services die (scrape fails). The trade-off: pull doesn't work well for ephemeral jobs → use Pushgateway for batch jobs.
