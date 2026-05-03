# Step 4 — Data Model and Storage

## Primary Table Schema

```sql
CREATE TABLE short_urls (
    short_code   CHAR(7)      NOT NULL PRIMARY KEY,
    long_url     TEXT         NOT NULL,
    user_id      BIGINT,                          -- null for anonymous
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMP,                       -- null = never
    click_count  BIGINT       NOT NULL DEFAULT 0  -- lazy updated
);

-- for dedup / custom-alias lookup
CREATE UNIQUE INDEX idx_long_url ON short_urls(md5(long_url));
```

## Why Relational (not NoSQL)?

| Criteria | RDBMS (MySQL/PG) | DynamoDB / Cassandra |
|----------|-------------------|----------------------|
| Schema simplicity | ✓ | ✓ |
| Atomic read-modify-write for click_count | ✓ | ✗ (needs transactions) |
| ACID durability | ✓ | Eventually consistent |
| Scale | Handles 6 B rows with sharding | Scales to 100s of TB |
| Operational complexity | Low | Higher |

**Verdict:** RDBMS is the right choice for v1 at this scale.  
Switch to DynamoDB or Cassandra when you exceed a single shard (~500 GB/node).

## Sharding Strategy (when needed)

```
Shard key = first 2 chars of short_code (62^2 = 3844 buckets)
Map buckets to shards in a ring:
  Shards 0-15  →  shard-1 (16 buckets)
  Shards 16-31 →  shard-2
  ...
```

Or use consistent hashing on `short_code`.

## Click Analytics (v2)

```
Do NOT write click_count synchronously on every redirect.
Instead:
  1. Redirect service publishes click event to Kafka
  2. Kafka consumer batches and does:
       UPDATE short_urls SET click_count = click_count + batch_size
     every 60 seconds
```

## Storage Tiering

```
Hot data (< 30 days):  MySQL primary + Redis
Warm data (30d - 1yr): MySQL read replicas
Cold data (> 1 year):  Archive to S3 (Parquet), query via Athena
Expired URLs:          Nightly cron DELETE WHERE expires_at < NOW()
```
