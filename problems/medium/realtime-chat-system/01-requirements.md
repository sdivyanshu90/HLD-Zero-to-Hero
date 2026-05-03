# Step 1 — Requirements

## Functional Requirements

| # | Requirement |
|---|-------------|
| F1 | Send and receive messages in real-time |
| F2 | 1:1 and group chats (≤ 500 members) |
| F3 | Message history / persistence |
| F4 | Online / offline presence indicator |
| F5 | Read receipts (delivered + seen) |
| F6 | Message ordering guarantees |
| F7 | File and image sharing (v2) |
| F8 | End-to-end encryption (v2) |

## Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| N1 | DAU | 50 M |
| N2 | Messages/day | 50 M × 20 = 1 B messages/day |
| N3 | Latency | Message delivery < 100ms (same region) |
| N4 | Durability | No message loss; at-least-once delivery |
| N5 | Availability | 99.99% for message sending |

## Capacity Estimation

```
Messages/day: 1 B
Write QPS:    1 B / 86 400 ≈ 11 600 msg/sec
Peak:         3× ≈ 35 000 msg/sec
Avg msg size: 500 B
Write BW:     35 000 × 500 B ≈ 17 MB/s
Storage/year: 1 B × 365 × 500 B = 182 TB → need distributed storage
```
