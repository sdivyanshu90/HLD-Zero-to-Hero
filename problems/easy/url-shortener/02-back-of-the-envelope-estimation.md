# Step 2 — Back-of-the-Envelope Estimation

## Scale Assumptions

| Parameter | Value |
|-----------|-------|
| New URLs per month | 100 M |
| Read : Write ratio | 10 : 1 |
| URL lifetime | 5 years |
| Avg original URL size | 200 B |
| Avg row size in DB | 500 B (short_code + long_url + metadata) |

## QPS Calculation

```
Write QPS  = 100 M / (30 × 86 400)  ≈ 40 writes/sec
Peak write = 40 × 3 (spike factor)  ≈ 120 writes/sec

Read QPS   = 40 × 10               = 400 reads/sec
Peak read  = 400 × 3               ≈ 1 200 reads/sec
```

## Storage Calculation

```
Rows over 5 years = 100 M/mo × 12 × 5 = 6 B rows
Storage           = 6 B × 500 B       = 3 TB
With 3× replication                   = 9 TB total
```

## Namespace (Key Space)

```
base62 alphabet: 0-9 a-z A-Z  →  62 characters
7-character code: 62^7 = 3 521 614 606 208  ≈ 3.5 T unique codes
Required codes: 6 B  →  well within space (< 0.2 % utilised)
```

## Bandwidth

```
Write: 120 req/sec × 200 B long URL  =  24 KB/s inbound
Read:  1 200 req/sec × ~50 B        =  60 KB/s outbound (headers only)
```

## Cache Sizing

```
Top 20 % of URLs get 80 % of traffic (Pareto)
Unique hot URLs: 6 B × 20 %  =  1.2 B  (too many for Redis)
Redis stores daily hot set:
  1 200 req/s × 86 400 s × 20 % unique ≈ 20 M entries × 300 B ≈ 6 GB  ✓
```

## Interviewer Summary Line

> "40 writes/sec, 400 reads/sec, 3 TB over 5 years. A single DB handles writes easily; Redis absorbs 80 %+ of reads."
