# Ticket Booking System — System Design Walkthrough

**Difficulty:** Medium  
**Tags:** concurrency, pessimistic-locking, Redis, distributed-lock, saga  
**Companies:** BookMyShow, Ticketmaster, Eventbrite

---

## Problem Statement

Design a ticket booking system that:
- Handles millions of users trying to book limited seats simultaneously
- Prevents double-booking (seat assigned to ≤ 1 user)
- Provides a temporary hold/reservation period (10 minutes)
- Scales for flash sales (100K concurrent users for 10K tickets)

---

## Architecture Diagram

```
Users
  │
  ▼
┌──────────────────┐
│   API Gateway    │  rate limiting per user/IP
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│          Booking Service                  │
│  1. Check availability  (Redis)           │
│  2. Reserve seat         (Redis NX lock) │
│  3. Create hold record   (DB)            │
│  4. Process payment      (Payment Svc)   │
│  5. Confirm booking      (DB)            │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 ┌──────┐  ┌──────┐  ┌──────────┐
 │Redis │  │MySQL │  │Payment   │
 │(hold)│  │(seats│  │Service   │
 │      │  │ DB)  │  │          │
 └──────┘  └──────┘  └──────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic and Contention Model](02-traffic-and-contention-model.md)
3. [API Design](03-api-design.md)
4. [Seat Inventory Data Model](04-seat-inventory-data-model.md)
5. [Concurrency Control](05-concurrency-control.md)
6. [Caching and Read Optimization](06-caching-and-read-optimization.md)
7. [Payment and Saga Flow](07-payment-and-saga-flow.md)
8. [Checkpoint](08-checkpoint.md)
