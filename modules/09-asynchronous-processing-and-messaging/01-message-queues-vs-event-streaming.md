# Message Queues vs Event Streaming

## The Core Distinction

Both systems decouple producers from consumers. But they differ fundamentally in semantics, retention, and use case.

```
Message Queue (RabbitMQ, SQS):
  - Message sent → consumed ONCE → deleted
  - Queue is a transient buffer: messages exist to be delivered, then gone
  - Producer doesn't know which consumer handles which message
  - Think: task queue, job queue

Event Stream (Kafka, Kinesis):
  - Events written → retained for N days (e.g., 7 days)
  - Any number of consumers can read the same event
  - Consumer tracks its own "offset" (position in the stream)
  - Think: append-only log, event sourcing, real-time analytics
```

---

## Message Queue Architecture (RabbitMQ)

```
Producer ──▶ Exchange ──▶ Queue ──▶ Consumer 1
                     └──▶ Queue ──▶ Consumer 2

Exchange types:
  Direct:  route to queue whose binding key exactly matches routing key
  Fanout:  route to ALL bound queues (broadcast)
  Topic:   route using wildcard matching (orders.*.success)
  Headers: route based on message header values

Work queue pattern:
  Multiple consumers on same queue:
    Producer → Queue → [Consumer A, Consumer B, Consumer C]
    Message delivered to exactly ONE consumer (round-robin or weighted)
    Consumer ACKs → message deleted
    Consumer crashes → message requeued → another consumer retries
  
  Use for: background job processing, email sending, image resizing
```

### Message Acknowledgment

```
Manual ACK (reliable delivery):
  1. Consumer receives message
  2. Consumer processes it
  3. Consumer sends ACK → broker deletes message
  4. If consumer crashes before ACK: broker redelivers to another consumer

  Basic consume:
    channel.basic_consume(queue='tasks', on_message_callback=process)
    def process(ch, method, properties, body):
        do_work(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)  # ACK after success

Auto-ACK (fast but unreliable):
  Broker considers message delivered immediately on send
  If consumer crashes before processing: message LOST
  Use only for non-critical, idempotent workloads where loss is OK

Dead Letter Queue (DLQ):
  Message fails processing N times → moved to DLQ
  Ops team inspects DLQ: diagnose failures, replay manually
  Every production queue should have a DLQ
```

---

## Event Streaming Architecture (Kafka)

```
                    Kafka Cluster
  ┌────────┐   ┌─────────────────────────────────────┐
  │Producer│──▶│  Topic: orders                       │
  │        │   │  ┌──────────┬──────────┬──────────┐  │
  └────────┘   │  │Partition0│Partition1│Partition2│  │
               │  │[0,1,2,3] │[0,1,2,3] │[0,1,2,3] │  │
               │  └──────────┴──────────┴──────────┘  │
               └─────────────────────────────────────┘
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
             Consumer    Consumer    Consumer
             Group A:1   Group A:2   Group A:3
             (analytics)(fraud det) (warehouse)

Key Kafka concepts:
  Topic: named stream of events
  Partition: ordered, immutable log; events appended to end
  Offset: position within a partition (each consumer tracks its own)
  Consumer Group: N consumers sharing partitions of a topic (each partition owned by 1 consumer in group)
  Retention: events kept for N days regardless of consumption
```

### Kafka vs Message Queue Summary

```
Aspect            Message Queue (SQS/RabbitMQ)    Kafka
──────────────────────────────────────────────────────────────────
Message retention   Deleted after consumption    Retained for days/weeks
Consumer model      Competing consumers          Multiple independent consumer groups
Replay              Not possible                 Yes (seek to any offset)
Ordering            Per-queue (no partition key) Per-partition (ordered within partition)
Throughput          Moderate (100K msg/s)        Very high (millions/s)
Use case            Task queues, work distribution  Event sourcing, stream processing, audit log
Typical systems     Email sending, job queuing   Clickstream, CDC, real-time analytics
```

---

## When to Use What

```
Use a Message Queue (SQS, RabbitMQ) when:
  ✓ Task distribution: send job to one of N workers (one-to-one delivery)
  ✓ At-least-once processing of discrete tasks
  ✓ Dead-letter queue for failed tasks
  ✓ Simple producer-consumer with no replay needs
  Examples: email delivery, image processing, payment processing

Use Kafka (Event Streaming) when:
  ✓ Multiple consumers need the same events (fan-out to many services)
  ✓ Replay: reprocess events from beginning or a specific time
  ✓ Event sourcing: system state derived from event log
  ✓ High throughput ingestion (logs, metrics, clickstream)
  ✓ Change Data Capture (CDC): stream DB changes to other systems
  Examples: user activity tracking, microservice event bus, real-time analytics
```

---

## Interview Quick Answers

- **What is the key difference between Kafka and RabbitMQ?** — RabbitMQ is a message broker: messages are consumed once then deleted, multiple consumers compete for messages. Kafka is an event log: messages are retained for a configurable period, any number of independent consumer groups can read the same events with independent offsets.
- **When would you use a message queue over Kafka?** — For task distribution where each task should be done exactly once by one worker (email sending, background jobs). Kafka is overkill here and adds operational complexity. Use queues for simple async work, Kafka for event buses and streaming.
