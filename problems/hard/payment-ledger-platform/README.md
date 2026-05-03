# Payment Ledger Platform — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** double-entry bookkeeping, idempotency, ACID, ledger, reconciliation  
**Companies:** Stripe, PayPal, Square, Shopify Payments

---

## Problem Statement

Design a payment ledger platform that:
- Processes 1 M transactions/day with exact accounting
- Ensures no money is created or destroyed (double-entry accounting)
- Supports idempotent payments (retry-safe)
- Provides balance queries with < 100ms latency
- Enables reconciliation and audit trails

---

## Architecture Diagram

```
Client / Payment Initiator
         │
         ▼
┌──────────────────────────┐
│   Payment API Service    │  idempotency key validation
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────────────────────┐
│         Ledger Service                    │
│  1. Validate (accounts exist, balances)  │
│  2. BEGIN SERIALIZABLE transaction       │
│  3. INSERT two ledger entries            │
│  4. UPDATE account balances              │
│  5. COMMIT                               │
└───────────────────────┬──────────────────┘
                        │
           ┌────────────┴────────────┐
           ▼                         ▼
┌────────────────┐       ┌────────────────────┐
│  Postgres DB   │       │  Kafka (events)    │
│  (SERIALIZABLE)│       │  payment_completed │
└────────────────┘       └────────────────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Accounting Model and Invariants](02-accounting-model-and-invariants.md)
3. [API and Idempotency](03-api-and-idempotency.md)
4. [Ledger Storage and Double-Entry](04-ledger-storage-and-double-entry.md)
5. [Balance Computation and Read Models](05-balance-computation-and-read-models.md)
6. [Settlement and Reconciliation](06-settlement-and-reconciliation.md)
7. [Failure Handling and Auditability](07-failure-handling-and-auditability.md)
8. [Checkpoint](08-checkpoint.md)
