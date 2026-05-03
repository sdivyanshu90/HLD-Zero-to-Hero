# Metrics, Monitoring, and Alerting — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** TSDB, Prometheus, InfluxDB, cardinality, downsampling, alerting  
**Companies:** Datadog, New Relic, Grafana Labs, Splunk

---

## Problem Statement

Design a metrics monitoring and alerting platform (like Datadog) that:
- Ingests 100 K metrics/second from 10 K services
- Stores time-series data at 1-second resolution for 15 days
- Supports ad-hoc queries with < 2s latency
- Fires alerts within 60 seconds of a metric crossing a threshold

---

## Architecture Diagram

```
Services / Hosts
    │ push (StatsD/OTLP) or pull (Prometheus scrape)
    ▼
┌─────────────────────┐
│  Collector Layer    │  aggregation, validation, routing
│  (Kafka / Agent)    │
└────────┬────────────┘
         │
    ┌────┴───────┐
    ▼            ▼
┌──────────┐  ┌──────────────────────┐
│  TSDB    │  │   Alert Engine       │
│(Thanos/  │  │ (Prometheus rules)   │
│ M3DB)    │  └──────────────────────┘
└──────────┘         │
    │                ▼
    ▼         ┌────────────┐
  Grafana     │ PagerDuty  │
  Dashboard   │ / Slack    │
              └────────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Ingestion and Cardinality](02-ingestion-and-cardinality.md)
3. [Time-Series Storage](03-time-series-storage.md)
4. [Querying and Downsampling](04-querying-and-downsampling.md)
5. [Alert Evaluation Pipeline](05-alert-evaluation-pipeline.md)
6. [Tenant Isolation and Retention](06-tenant-isolation-and-retention.md)
7. [Failures and Backpressure](07-failures-and-backpressure.md)
8. [Checkpoint](08-checkpoint.md)
