# Step 2 — Throughput and Capacity

## Target Load

```
Total cluster target: 1 M IDs/sec
Nodes planned:        10
Per-node target:      100 K IDs/sec
Snowflake per-node:   4.096 M IDs/sec  ← 40× headroom
```

## Timestamp Capacity

```
41-bit millisecond timestamp:
  2^41 = 2 199 023 255 552 ms
       = 2 199 023 255 s
       ÷ 86 400 s/day  ÷ 365.25 days/yr
       ≈ 69.7 years

Custom epoch (Jan 1, 2020):
  Useful until year 2020 + 69 = 2089
```

## Machine ID Capacity

```
10-bit machine ID: 2^10 = 1024 unique nodes

If you have multiple data centres:
  5 bits = data centre ID (32 DCs)
  5 bits = worker ID within DC (32 workers per DC)
  Total:  32 × 32 = 1024 nodes
```

## Sequence Capacity

```
12-bit sequence: 2^12 = 4096 IDs per millisecond per node
At 1 ms tick:    4096 guaranteed unique IDs
At clock rollover: wait for next ms
```

## Scale Summary

```
1 node   →  4.1 M IDs/sec
10 nodes →  41 M IDs/sec
1024 nodes (max) → 4.2 B IDs/sec
```
