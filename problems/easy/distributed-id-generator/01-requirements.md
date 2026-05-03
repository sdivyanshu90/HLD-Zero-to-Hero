# Step 1 — Requirements

## Functional Requirements

| # | Requirement |
|---|-------------|
| F1 | Generate globally unique IDs |
| F2 | IDs are 64-bit unsigned integers |
| F3 | IDs are sortable by generation time |
| F4 | IDs are monotonically increasing within a machine |
| F5 | No central bottleneck on the hot path |

## Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| N1 | Throughput | ≥ 1 M IDs/sec across cluster |
| N2 | Latency | < 1 ms per ID generation |
| N3 | High availability | No single point of failure |
| N4 | Clock safety | Handle NTP jumps / clock skew |

## Clarifying Questions

1. "Should IDs be globally sortable (across machines) or just locally monotonic?"
2. "Is a 64-bit ID required, or is 128-bit (UUID) acceptable?"
3. "What's the expected lifetime of the system? (affects epoch choice)"
4. "How many generator nodes will run concurrently?"
5. "What should happen if the system clock goes backward?"

## Non-Goals

- Human-readable IDs
- Sequential gap-free IDs (gaps are acceptable when nodes restart)
- Cryptographically unpredictable IDs (use UUIDv4 for security tokens)
