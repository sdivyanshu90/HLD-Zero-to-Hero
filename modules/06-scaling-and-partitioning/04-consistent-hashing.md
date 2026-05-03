# Consistent Hashing

Naive `hash(key) % N` remaps a large fraction of keys when the node count changes. Consistent hashing reduces that disruption.

## Core Idea

Hash both nodes and keys onto a ring. Each key is assigned to the first node clockwise from it.

## Why It Helps

When a node joins or leaves, only a slice of keys moves instead of nearly all keys.

## Real-World Analogy

Imagine houses placed around a circular road and mail zones assigned to the next post office clockwise. Adding one post office only affects nearby houses.

## Trade-Offs

- Better churn behavior than naive modulo hashing.
- Still requires replication, rebalancing limits, and hot-key mitigation.

## Interview Use

Use this when node membership changes and you want to avoid massive remapping.
