# Step 3 — Kafka and Partitioning

## Topic Design

```
Topic: ad-clicks-raw
  Partitions: 200
  Replication factor: 3
  Retention: 7 days (raw event replay)
  Compression: lz4

Topic: ad-clicks-aggregated-1min
  Partitions: 50
  Retention: 30 days

Topic: ad-clicks-aggregated-1hour
  Partitions: 20
  Retention: 90 days
```

## Partition Key Strategy

```
Option A: hash(ad_id)
  → All clicks for same ad go to same partition
  → Sequential processing per ad
  → Risk: viral ad overloads one partition

Option B: hash(campaign_id)
  → Balance at campaign level
  → More uniform distribution

Option C: hash(ad_id + time_bucket_1min)
  → Distributes even popular ads across time
  → Best for aggregation workers (all data for a time-window co-located)

Recommendation: Option C for aggregation topics
               Option B for raw events (more uniform)
```

## Throughput Math

```
500 K events/sec peak
1 KB per event
Throughput: 500 MB/s

Kafka per-partition throughput: ~50 MB/s
Partitions needed: 500 / 50 = 10 (with headroom → use 200)

Producer batching:
  batch.size = 1 MB
  linger.ms  = 5 ms
  → reduces 500K individual sends to ~500 batch sends/sec
  → 1000× reduction in network round-trips
```

## Consumer Group Design

```
Consumer group: flink-streaming-agg
  Each Flink task manager owns N partitions
  State: aggregation windows stored in RocksDB (Flink state backend)

Consumer group: spark-batch-billing
  Reads same raw topic (different offset)
  Runs hourly for exact billing counts

Consumer group: s3-archiver
  Writes raw events to S3 Parquet for long-term storage
  Enables replay for backfill
```
