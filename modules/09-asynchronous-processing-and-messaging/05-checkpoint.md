# Module 09 Checkpoint: Asynchronous Processing and Messaging

## Questions

---

**Q1.** An order service needs to: (a) charge a credit card, (b) reduce inventory, (c) send a confirmation email. All three steps should succeed or none should. How do you design this?

> **Answer:** This is a distributed transaction problem. Options:
> 1. **SAGA with choreography** (recommended): OrderCreated event → Payment Service charges card → publishes PaymentCharged → Inventory Service reserves stock → publishes InventoryReserved → Email Service sends confirmation. If payment fails: publish PaymentFailed, compensating transaction releases any inventory reservation. Each step is locally atomic; overall consistency is eventual.
> 2. **SAGA with orchestration**: Central OrderOrchestrator calls each service in sequence, tracks state, calls compensating transactions on failure. Simpler to debug but orchestrator can be a bottleneck.
> 3. **Outbox Pattern**: Order Service writes order + outbox record to DB in one transaction. Background process reads outbox and publishes to Kafka. Ensures at-least-once delivery without dual-write risk.

---

**Q2.** A Kafka consumer processes payment events. The consumer crashes after writing to the payments table but before committing its offset. What happens on restart?

> **Answer:** The consumer restarts and reads from its last committed offset — which is BEFORE the payment it already processed. It processes the same payment event again. Without idempotency: **duplicate payment** (charged twice!). Fix: use an idempotency key (payment_id) stored with the payment record. `INSERT INTO payments (payment_id, ...) ON CONFLICT (payment_id) DO NOTHING`. Second processing: conflict → no-op → safe.

---

**Q3.** How would you implement exactly-once delivery from Kafka to PostgreSQL?

> **Answer:** Store the Kafka offset in PostgreSQL and use a DB transaction:
> ```python
> with db.begin():
>     # Process the event
>     db.execute("INSERT INTO events ...", data)
>     # Save the offset in the same transaction
>     db.execute("INSERT INTO kafka_offsets (topic, partition, offset) VALUES (%s,%s,%s) ON CONFLICT ... DO UPDATE SET offset=%s", ...)
>     db.commit()
> ```
> On restart: read last committed offset from DB → seek consumer to that offset → resume exactly where you left off. The key: offset stored atomically with the processed data → exactly-once semantics.

---

**Q4.** You have 3 Kafka partitions and 5 consumers in a consumer group. What is the partition assignment?

> **Answer:** Kafka assigns at most 1 partition per consumer. With 3 partitions and 5 consumers: 3 consumers get 1 partition each, 2 consumers sit idle (no partition to consume). To scale consumption: add more partitions (partitions must be >= consumers for all consumers to be active). Rule: `effective_parallelism = min(partitions, consumers)`.

---

**Q5.** What is the difference between PULL and PUSH consumer models? Which does Kafka use?

> **Answer:**
> - **Push (RabbitMQ/SQS)**: broker pushes messages to consumer as soon as available. Consumer must handle whatever rate broker sends. Can overwhelm slow consumers.
> - **Pull (Kafka)**: consumer polls (`consumer.poll()`) at its own pace. Consumer controls the rate. Naturally handles backpressure: if consumer is slow, it just polls less frequently. Broker doesn't need to track consumer state (offset tracking is done by consumer).
> - Kafka uses PULL. Benefits: consumer backpressure, batch reads (pull many messages at once), consumer can rewind/replay by changing offset.

---

## Checklist

- [ ] Message queue vs event stream: delivered-once vs retained log
- [ ] RabbitMQ: exchange types, manual ACK, DLQ
- [ ] Kafka architecture: topic, partition, offset, consumer group, broker
- [ ] Consumer groups: independent offsets, partition assignment (1 partition per consumer max)
- [ ] At-least-once: retry on failure, requires idempotent processing
- [ ] Exactly-once: idempotency keys, Kafka transactions, external offset storage
- [ ] Saga pattern: distributed transactions via compensating transactions
- [ ] Kafka producer: batching, compression, idempotent producer, acks levels
- [ ] ISR: in-sync replicas, acks=all guarantees
- [ ] Log compaction vs retention: snapshot vs time-windowed
- [ ] Exponential backoff with jitter: prevent retry storms
