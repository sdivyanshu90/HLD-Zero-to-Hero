# Kafka Internals: Partitions, Offsets, and Throughput

## Kafka's Log Architecture

Kafka's fundamental unit is the **partition**: an ordered, immutable, append-only log:

```
Topic: user-events, Partition 0:

  Offset: 0    1    2    3    4    5    6    7    8
         [e0] [e1] [e2] [e3] [e4] [e5] [e6] [e7] [e8] → new events append here

  Log segment files on disk:
    00000000000000000000.log  (offsets 0-999,999)
    00000000000001000000.log  (offsets 1M-1,999,999)
    00000000000002000000.log  (offsets 2M+)
    ...each segment ~1 GB (configurable)
  
  Index file (per segment):
    00000000000000000000.index  → sparse index: offset → byte position in log
    Allows O(log N) seek to any offset (binary search in index)
```

---

## Producer Internals

```
Producer publishes to a partition:
  1. Determine partition:
     - Explicit: producer.send("topic", key, value) → partition = hash(key) % numPartitions
     - Round-robin: no key → cycle through partitions
     - Custom: implement Partitioner interface
  
  2. Batch records:
     ProducerRecord → RecordAccumulator (in-memory buffer)
     RecordBatch: accumulate until batch.size (16KB) OR linger.ms (0ms default)
     → send batch to broker
  
  3. Compression:
     Compress entire batch (lz4, snappy, gzip, zstd)
     Typical ratio: 2-4× compression for JSON/text events
  
  4. Retry on failure:
     retries = MAX_INT (default in modern Kafka)
     Idempotent producer: no duplicates on retry
     delivery.timeout.ms = 120s (total allowed retry window)

Throughput optimization:
  batch.size = 1MB (from 16KB default) → larger batches, fewer network calls
  linger.ms = 10ms (wait 10ms to fill larger batches) → ~10× throughput gain
  compression.type = lz4 → 3× less network + disk bandwidth
  acks = 1 (only leader ACK, no ISR wait) → lower latency, higher throughput
```

---

## Partition and Replication

```
Kafka topic with 3 partitions, replication factor = 3:

  Broker 1    Broker 2    Broker 3
  ────────────────────────────────
  P0 (leader)   P0 (follower)   P0 (follower)
  P1 (follower) P1 (leader)     P1 (follower)
  P2 (follower) P2 (follower)   P2 (leader)

ISR: In-Sync Replicas
  Set of replicas that are "caught up" with the leader
  (within replica.lag.time.max.ms, default 30s)
  
  acks=all (acks=-1): leader waits for ALL ISR members to ACK before confirming write
  → If only 2 of 3 are in ISR: waits for 2 ACKs
  → Durable but slower (waits for slowest ISR member)
  
  acks=1: only leader ACKs
  → Faster but if leader fails before replication: data loss
  
  Unclean leader election:
    If ALL ISR members fail, elect out-of-sync replica as leader?
    unclean.leader.election.enable=true → possible data loss but available
    unclean.leader.election.enable=false → stop partition (CP behavior)
```

---

## Throughput Numbers

```
Kafka throughput (well-tuned cluster):
  Single partition:    ~50-100 MB/s (disk I/O bound)
  Single broker:       ~500 MB/s (with multiple partitions)
  3-node cluster:      1-2 GB/s (across all partitions)
  Production at LinkedIn: 7 TB/day ingested, 2M messages/second

Consumer throughput:
  Single consumer per partition: ~50-100 MB/s
  Multiple consumer groups: each at full throughput independently
  (Kafka doesn't slow down under multiple consumer groups — sequential reads are fast)

Why Kafka is fast:
  Sequential disk writes: appending to partition log → HDD sequential = 100 MB/s+
  Zero-copy transfer: sendfile() syscall → data goes disk → network without user-space copy
  Batching: many messages per network call
  Compression: less network bandwidth
  OS page cache: hot partition data served from RAM, not disk
```

---

## Kafka Retention and Compaction

```
Log retention (default):
  retention.ms = 7 days (delete segments older than 7 days)
  retention.bytes = -1 (unlimited by size unless set)
  
  Cleanup on retention:
    Oldest log segments deleted automatically
    Consumers that fall too far behind may miss messages (consumer lag issue!)
    Monitor: consumer_lag metric → alert if growing

Log compaction (cleanup.policy=compact):
  Instead of deleting old segments: keep only the LATEST value per key
  
  Before compaction:
    Offset 1: key=user:1, value={name:"Alice"}
    Offset 5: key=user:1, value={name:"Alice Smith"}  ← update
    Offset 10: key=user:2, value={name:"Bob"}
    Offset 15: key=user:1, value=null                  ← delete (tombstone)
  
  After compaction:
    key=user:1: tombstone (deleted)
    key=user:2: {name:"Bob"}
    (older values for user:1 removed)
  
  Use case: materializing latest state from event stream
  Kafka as a source of truth for database-like semantics (event sourcing)
  Consumers can replay from the beginning to rebuild current state
```

---

## Kafka vs Alternatives

```
System          Throughput    Retention  Use case
────────────────────────────────────────────────────────────────
Kafka           Very high     Configurable  Event streaming, CDC, analytics
RabbitMQ        High          Short (hours) Task queues, work distribution
AWS SQS         Medium        4-14 days    Simple async tasks (managed)
AWS Kinesis     High          7 days        AWS-native streaming (less config)
Google Pub/Sub  High          7 days        GCP-native, simpler ops
NATS            Very high     None          Ultra-low latency messaging
Redis Streams   High          Configurable  Simple streaming, Redis-native
```

---

## Interview Quick Answers

- **How does Kafka achieve such high throughput?** — Sequential disk writes (much faster than random), batching (many messages per network/disk I/O), compression (3× bandwidth reduction), zero-copy transfers (sendfile syscall bypasses user space), OS page cache (hot partitions served from RAM).
- **What is the ISR in Kafka?** — In-Sync Replicas: the set of partition replicas that are current with the leader. `acks=all` requires all ISR members to acknowledge a write before the producer receives a success response. This ensures no data loss if the leader fails (a new leader elected from ISR has all committed data).
- **When would you use log compaction vs log retention?** — Log retention: drop messages older than N days (streaming use case; consumers process in real-time). Log compaction: keep only the latest value per key (snapshot/changelog use case; consumer can rebuild current state by replaying from offset 0).
