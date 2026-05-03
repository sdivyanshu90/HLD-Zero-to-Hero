# Food Delivery Platform — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** order-lifecycle, geospatial, ETA, dispatch, saga, real-time  
**Companies:** DoorDash, Uber Eats, GrubHub, Deliveroo

---

## Problem Statement

Design a food delivery platform (like DoorDash) that:
- Handles 10 M orders/day with end-to-end order lifecycle
- Matches couriers to orders within 60 seconds
- Provides accurate ETA to customers (prep + delivery time)
- Handles order state transitions reliably with saga pattern

---

## Order Lifecycle State Machine

```
CREATED → PAYMENT_PENDING → CONFIRMED → PREPARING
    ↓                                       ↓
CANCELLED                              READY_FOR_PICKUP
                                            ↓
                                   COURIER_ASSIGNED
                                            ↓
                                     PICKED_UP
                                            ↓
                                    DELIVERED (terminal)
                                            |
                               DELIVERY_FAILED (terminal)
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic and Entity Model](02-traffic-and-entity-model.md)
3. [Order and Restaurant Flow](03-order-and-restaurant-flow.md)
4. [Courier Dispatch and Location](04-courier-dispatch-and-location.md)
5. [Menu Cache and Read Scaling](05-menu-cache-and-read-scaling.md)
6. [Order State and Payment Saga](06-order-state-and-payment-saga.md)
7. [Delays, Cancellations, and Failures](07-delays-cancellations-and-failures.md)
8. [Checkpoint](08-checkpoint.md)
