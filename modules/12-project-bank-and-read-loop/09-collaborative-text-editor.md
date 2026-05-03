# Cheat Sheet: Collaborative Text Editor

## Scale (BoE)
```
Users per document: 10-100 concurrent editors
Operations per user: ~100 keystrokes/minute = ~2 ops/second
Total OPS for 100 users: 200 ops/second per document
Documents: 1M+ active documents
```

## The Core Problem: Concurrent Edits

```
User A and User B both have document: "Hello"
A inserts "W" at position 0 → "WHello"
B deletes "H" at position 1 → "ello"

Without coordination:
  A's op reaches B: insert "W" at pos 0 → "Wello" (B's delete at 1 deleted "e"!)
  
This is the "operational transformation" problem.
```

## Operational Transformation (OT)

```
Transform operation based on concurrent operations received:
  A's op: Insert("W", pos=0)
  B's op: Delete("H", pos=1)
  
  At server: A's op comes first → apply A's op → document = "WHello"
  Now transform B's op to account for A's insertion:
    B's delete was at pos 1 (before A's insert at pos 0)
    After A inserts at pos 0, the "H" is now at pos 2
    Transform B's op: Delete("H", pos=2)
  Apply transformed B's op → "Wello"

OT requires central server for ordering (linearization of operations)
Used by: Google Docs (original implementation)
Complex to implement correctly (especially for rich text)
```

## CRDT (Conflict-free Replicated Data Types)

```
Alternative: assign each character a unique ID
  'H' → {id: "A:1", value: "H"}
  'e' → {id: "A:2", value: "e"}
  
  A inserts 'W' before 'H': {id: "B:1", value: "W", after: null, before: "A:1"}
  B deletes 'H': {id: "A:1", tombstone: true}
  
  Merge: apply all operations in any order → same result
  CRDT: no need for central server, can work peer-to-peer!
  
Used by: Figma (CRDT), Apple Notes (CRDT)
Libraries: Yjs, Automerge, ShareDB
```

## System Diagram
```
User A ──WebSocket──▶ Collaboration Server
                            │
                     Operation Queue
                            │
                     OT Transform Engine ──▶ Apply to doc state
                            │
                     Broadcast to all connected users (WebSocket)
                            │
                     Persist to: Redis (hot doc) + S3 (snapshots) + DB (history)
```

## Bottlenecks
1. Presence awareness: "Alice is editing line 5" → pub/sub per document, low frequency
2. Document snapshot: don't store every operation forever → snapshot every 1000 ops + replay delta

## Unique Trick
Vector clocks (or Lamport timestamps) are used to order concurrent operations across distributed servers. Each operation includes a vector clock, and the server merges operations by comparing their clocks.
