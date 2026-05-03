# Pub-Sub and Consumer Groups

## Publish-Subscribe Pattern

Pub-sub decouples publishers (producers) from subscribers (consumers) through a topic abstraction:

```
Traditional point-to-point:
  Order Service ──────────────────────▶ Email Service
              └─────────────────────────▶ Inventory Service
              └─────────────────────────▶ Analytics Service
  → Order Service must know about all downstream services
  → Adding new service = modifying Order Service

Pub-Sub:
  Order Service ──▶ [Topic: order.created] ──▶ Email Service
                                           ──▶ Inventory Service
                                           ──▶ Analytics Service
  → Order Service publishes to topic, knows nothing about consumers
  → New service subscribes to topic, Order Service unchanged
  → Loose coupling!
```

---

## Kafka Consumer Groups: The Key Abstraction

```
Topic: user-events (3 partitions)
  Partition 0: [e1, e5, e9, e13...]
  Partition 1: [e2, e6, e10, e14...]
  Partition 2: [e3, e7, e11, e15...]

Consumer Group A (analytics): 3 consumers
  Consumer A1 → Partition 0 (processes e1, e5, e9...)
  Consumer A2 → Partition 1 (processes e2, e6, e10...)
  Consumer A3 → Partition 2 (processes e3, e7, e11...)
  
  Each consumer in group A reads a distinct subset
  Together, group A processes ALL events exactly once (per group)

Consumer Group B (fraud detection): 2 consumers
  Consumer B1 → Partitions 0+1 (handles 2 partitions)
  Consumer B2 → Partition 2
  
  Group B ALSO processes ALL events, independent of Group A
  Offsets for Group A and Group B are tracked separately

Consumer Group C (data warehouse): 1 consumer (slow batch)
  Consumer C1 → ALL 3 partitions (but slower, behind by hours)
  Group C reads all events at its own pace, independent of A and B

Key insight:
  ONE event stream → multiple independent consumers
  Each group tracks its OWN offset per partition
  No coordination needed between groups!
```

---

## Partition Assignment and Rebalancing

```
Consumer group with 3 consumers, topic with 4 partitions:
  
  Initial assignment:
    Consumer 1 → Partitions 0, 3  (2 partitions)
    Consumer 2 → Partition 1
    Consumer 3 → Partition 2
  
  Consumer 2 crashes:
    Group coordinator detects (heartbeat timeout, ~10 seconds)
    Rebalancing triggered:
    Consumer 1 → Partitions 0, 1  (takes P1 from crashed C2)
    Consumer 3 → Partitions 2, 3  (takes P3 from C1, plus P2)
  
  Cost of rebalancing:
    During rebalancing: consumers STOP processing (Stop-the-world!)
    Rebalance duration: typically 2-30 seconds
    Mitigations:
      - Incremental cooperative rebalancing (Kafka 2.4+): only reassign affected partitions
      - Static group membership (group.instance.id): temporary consumer absence doesn't trigger rebalance
```

---

## Offset Management

```
Offset: position of consumer in a partition's log

Offset commit:
  After processing a batch, consumer commits offset to Kafka broker
  Broker stores committed offsets in __consumer_offsets topic
  
  On restart/rebalance: consumer resumes from last committed offset
  
  Commit timing options:
    Auto-commit (enable.auto.commit=true):
      Kafka commits offset every 5 seconds (default auto.commit.interval.ms)
      Risk: consumer processes messages then crashes before auto-commit
      → On restart: re-processes last 5 seconds of messages (at-least-once)
    
    Manual commit after processing:
      Process batch → verify success → commitSync()
      Guarantees: no message "lost" (not processed without commit)
      Still at-least-once (commit after crash = reprocessing on restart)
    
    Manual commit before processing:
      commitSync() → process batch
      At-most-once: if crash after commit but before processing → message skipped
      Use only when losing a message is better than processing it twice

Offset tracking strategies:
  Kafka-managed offsets: stored in Kafka broker (standard approach)
  External offsets: stored in your own DB (allows transactional offset + processing)
    → Enables exactly-once by writing processed result + new offset in same DB transaction
```

---

## Dead Letter Topics in Kafka

```
When a consumer fails to process a message repeatedly:

  Message → Consumer → process fails → retry (3 attempts) → give up
  → Publish to: topic-name.DLT (dead letter topic)
  → Continue processing next messages (don't block the partition)

Dead letter flow:
  orders topic → order consumer → fails after 3 retries
                                → publish to orders.DLT
  
  DLT consumer: alerting, debugging, manual replay

  Spring Kafka: @DltHandler annotation
  AWS SQS: MaxReceiveCount → dead-letter queue
  
  Important: DLT message should include:
    Original message content
    Reason for failure (exception message)
    Stack trace
    Retry count
    Original topic/partition/offset
```

---

## Redis Pub/Sub vs Kafka vs SQS

```
Feature           Redis Pub/Sub    Kafka              SQS
──────────────────────────────────────────────────────────────────
Persistence       NO (fire-forget) Yes (days/weeks)   Yes (4 days default)
Replay            NO               Yes (seek)          NO
Consumer groups   NO (all receive) Yes (independent)   Yes (standard queue)
At-least-once     NO (message lost if no subscriber)  Yes  Yes
Exactly-once      NO               Yes (with txns)     No (at-least-once)
Throughput        Very high (RAM)  Very high           Moderate
Ordering          No               Per-partition       FIFO queue option
Operational cost  Low              High                Very Low (managed)
Use case          Real-time signals, lightweight fan-out  Stream processing, CDC  Simple async tasks
```

---

## Interview Quick Answers

- **How do Kafka consumer groups enable fan-out?** — Each consumer group tracks its own offset per partition. Multiple groups can read the same topic independently. One group can be behind by hours (batch analytics) while another processes in real-time (fraud detection). This is fundamentally different from message queues where one consumer removes the message.
- **What happens to a Kafka consumer group during partition rebalancing?** — All consumers in the group stop processing (stop-the-world) while the group coordinator redistributes partitions. Typically takes 2-30 seconds. Kafka 2.4+ incremental cooperative rebalancing reduces this by only reassigning partitions that need to move.
