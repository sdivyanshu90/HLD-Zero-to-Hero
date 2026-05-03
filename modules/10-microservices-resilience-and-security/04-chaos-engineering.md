# Chaos Engineering

Chaos engineering is the deliberate injection of failure to verify that resilience claims are real.

## Why It Exists

Many systems look resilient in diagrams but fail under actual degraded conditions.

## Examples

- kill a node
- inject latency
- drop packets
- fail a dependency
- exhaust a resource pool

## Real-World Analogy

It is a fire drill for distributed systems.

## Trade-Offs

- It improves confidence and reveals hidden coupling.
- It must be controlled carefully to avoid avoidable production damage.

## Interview Use

Mention chaos engineering when the interviewer cares about mature operational discipline, not just architecture on paper.
