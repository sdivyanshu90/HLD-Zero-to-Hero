# Collaborative Text Editor — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** OT, CRDT, WebSocket, conflict resolution, operational transformation  
**Companies:** Google Docs, Notion, Figma, Dropbox Paper

---

## Problem Statement

Design a real-time collaborative text editor (like Google Docs) that:
- Allows multiple users to edit the same document simultaneously
- Merges concurrent edits without losing any changes
- Shows cursor positions of other users in real-time
- Scales to 10 M documents with thousands of simultaneous editors per document

---

## Concurrency Challenge

```
Document: "Hello"

User A (cursor at pos 5): inserts " World"  → "Hello World"
User B (cursor at pos 5): inserts " Earth"  → "Hello Earth"

Both see "Hello" when they start typing.
After merge, result should be: "Hello World Earth" or "Hello Earth World"
(deterministic, same on all clients)

This is the fundamental challenge: concurrent edit merging
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Concurrency and Data Shape](02-concurrency-and-data-shape.md)
3. [Session Architecture](03-session-architecture.md)
4. [OT vs CRDT](04-ot-vs-crdt.md)
5. [Ordering and Conflict Resolution](05-ordering-and-conflict-resolution.md)
6. [Persistence Pipeline](06-persistence-pipeline.md)
7. [Scaling Hot Documents](07-scaling-hot-documents.md)
8. [Checkpoint](08-checkpoint.md)
