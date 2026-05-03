# Split-Brain and Fencing Tokens

Split-brain happens when multiple nodes believe they are the valid writer or leader at the same time.

## Why It Is Dangerous

Two leaders can both accept writes, corrupting invariants or causing double execution.

## Fencing Tokens

A fencing token is a monotonically increasing identifier issued to the current leader or lock holder.

### Why It Helps

Storage or downstream systems can reject stale actors with older tokens.

## Real-World Analogy

Two people both think they have the key to the vault. A fencing token is a numbered work order that only the newest authorized worker can use.

## Trade-Offs

- Preventing split-brain usually requires coordination overhead.
- Fencing tokens improve safety but must be checked everywhere writes occur.

## Interview Use

If you mention failover, mention split-brain prevention. If you mention distributed locks, mention fencing tokens.
