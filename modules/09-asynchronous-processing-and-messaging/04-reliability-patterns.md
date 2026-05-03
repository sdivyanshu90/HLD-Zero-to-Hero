# Reliability Patterns

Asynchronous systems need explicit reliability patterns because retries and duplicates are normal, not exceptional.

## Dead Letter Queues

DLQs capture messages that repeatedly fail processing.

## Change Data Capture

CDC turns database changes into a reliable event stream.

## Idempotency Keys

Idempotency keys let a consumer or API safely ignore duplicate attempts.

## Delivery Semantics

At-least-once delivery may duplicate work. Exactly-once semantics are expensive and often depend on narrow definitions plus idempotent processing.

## Real-World Analogy

DLQ is the exception tray, CDC is copying official ledger changes into a broadcast log, and idempotency keys are stamped claim numbers that prevent repeated payouts.

## Interview Use

If you use retries, you must also explain duplicates and poison-message handling.
