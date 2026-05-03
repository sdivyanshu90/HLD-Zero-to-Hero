# Step 2 — Traffic and Fan-Out Model

## Volume Estimation

```
10 M notifications/day
= 10 M / 86400 s ≈ 116 notifications/sec (average)
Peak (evening):    ~5× = 580/sec
Product launch:    ~100× = 11 600/sec

Per channel split (assumed):
  Push:    60%  →  70 /sec avg
  Email:   25%  →  29 /sec avg
  SMS:     10%  →  12 /sec avg
  In-App:   5%  →  6  /sec avg
```

## Fan-Out Scenarios

```
1. Direct notification (1 → 1):
   "Your order #4521 has shipped"  →  single user
   
2. Broadcast (1 → N):
   "New product launch!"  →  5 M users
   Fan-out: write 5 M notification jobs to Kafka
   Rate: 5 M / 60 min = 83 K notifications/min

3. Social fan-out (user event → followers):
   "Alice posted a photo"  →  Alice's 10 K followers
   Similar to Twitter newsfeed fan-out
```

## Kafka Throughput

```
At 116 msg/sec with avg 1 KB each:
  Throughput: 116 KB/s (trivial for Kafka)
  Kafka can handle > 1 GB/s; headroom is enormous
  
Partition count per topic:
  high_priority:    8 partitions (parallelism for push workers)
  normal_priority:  16 partitions (bulk email/marketing)
  in_app:           4 partitions
```
