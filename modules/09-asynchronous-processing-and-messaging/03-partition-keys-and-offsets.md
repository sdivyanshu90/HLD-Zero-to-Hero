# Partition Keys and Offsets

Partitioning and offset tracking decide order, scaling, and replay behavior in streaming systems.

## Partition Keys

A partition key decides which partition an event lands on.

### Why It Matters

Events with the same key can preserve order within one partition.

## Offsets

An offset is a consumer's position in a partitioned log.

### Why It Matters

Offsets make replay, recovery, and exactly-where-I-left-off semantics possible.

## Trade-Offs

- Good partition keys preserve locality and ordering.
- Bad partition keys create hot partitions or destroy the ordering you need.

## Interview Use

If order matters per user, account, or ride, that entity often becomes the partition key.
