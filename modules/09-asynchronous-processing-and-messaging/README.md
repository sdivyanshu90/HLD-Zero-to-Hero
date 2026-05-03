# Module 09: Asynchronous Processing and Messaging

## Overview

Asynchronous messaging decouples services, enables horizontal scaling of processing, and provides natural backpressure. This module covers the full spectrum from simple task queues to sophisticated event streaming platforms.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│              MODULE 09 LEARNING MAP                             │
│                                                                  │
│  01-message-queues-vs-event-streaming                          │
│     └── Queue (task/once) vs Stream (log/many consumers)       │
│         RabbitMQ vs Kafka use cases                            │
│                    │                                            │
│                    ▼                                            │
│  02-pub-sub-and-consumer-groups                                 │
│     └── Topic fanout, consumer groups with independent offsets  │
│         Partition rebalancing, offset management               │
│                    │                                            │
│                    ▼                                            │
│  03-reliability-patterns                                        │
│     └── At-least-once (idempotent), exactly-once (txns)        │
│         Saga pattern, exponential backoff, DLQ                 │
│                    │                                            │
│                    ▼                                            │
│  04-kafka-internals                                             │
│     └── Log structure, ISR, throughput, compaction vs retention │
└────────────────────────────────────────────────────────────────┘
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-message-queues-vs-event-streaming.md](01-message-queues-vs-event-streaming.md) | Queue vs Stream paradigm |
| [02-pub-sub-and-consumer-groups.md](02-pub-sub-and-consumer-groups.md) | Fan-out, groups, offsets |
| [03-reliability-patterns.md](03-reliability-patterns.md) | At-least-once, exactly-once, Saga |
| [04-kafka-internals.md](04-kafka-internals.md) | Kafka deep dive |
| [05-checkpoint.md](05-checkpoint.md) | Self-test questions |
