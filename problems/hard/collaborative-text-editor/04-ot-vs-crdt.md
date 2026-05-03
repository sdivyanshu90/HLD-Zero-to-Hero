# Step 4 — OT vs CRDT

## Operational Transformation (OT)

```
Core idea: Transform an operation's position based on concurrent operations
           that have already been applied.

Operation: Insert(pos, char) or Delete(pos)

Example:
  State: "Hello"
  Op A: Insert(5, " World")   →  pos 5
  Op B: Insert(5, " Earth")   →  pos 5 (concurrent)

At server (receives A then B):
  Apply A: "Hello World"
  Transform B against A: B' = Insert(5+6, " Earth") = Insert(11, " Earth")
  Apply B': "Hello World Earth"

At Client A (receives B):
  Already applied A locally.
  Transform B against A: B' = Insert(11, " Earth")
  Apply B': "Hello World Earth"  ✓ (convergence!)
```

### OT Requirements

```
Properties:
  TP1: Transform(Op_a, Op_b) and Transform(Op_b, Op_a) produce same state
       (convergence after applying both)
  TP2: Required for groups of 3+ operations (harder to implement correctly)

Central server needed:
  Server is the authority on operation ordering
  Server timestamps ops; clients transform against all intervening ops

Libraries: ShareDB (Node.js), OT.js, Google Wave OT
```

## CRDT (Conflict-free Replicated Data Type)

```
Core idea: Data structure designed so all concurrent operations
           commute (order doesn't matter for final result)

For text: Logoot, LSEQ, RGA, Yjs (Yata algorithm)

Each character gets a globally unique ID:
  Char 'H' → ID(site=A, clock=1)
  Char 'e' → ID(site=A, clock=2)
  Char 'l' → ID(site=A, clock=3)
  ...

Insert always specifies (left_neighbor_ID, char):
  User A inserts ' ' after ID(A,5): [ID(A,6), ' ']
  User B inserts ' ' after ID(A,5): [ID(B,1), ' ']

Both ops can be applied in any order; tie-broken by site ID:
  Result: "Hello" + A's char + B's char (deterministic)
```

### CRDT Properties

```
No central server needed for conflict resolution
Operations can be applied in any order (commutative)
Peers can exchange ops directly (P2P possible)

Memory cost: each character stores its unique ID (~40 B overhead)
  1 MB document → ~40 MB CRDT state (40× amplification)

Garbage collection: tombstones (deleted chars still in structure)
  Requires periodic compaction

Libraries: Yjs (most popular), Automerge, ShareDB CRDT
```

## Comparison Table

| Aspect | OT | CRDT |
|--------|----|----|
| Algorithm complexity | High (TP2 is hard) | Moderate (ID assignment) |
| Memory overhead | Low | High (40× for text) |
| Central server needed | Yes (for ordering) | No (can be P2P) |
| Network topology | Hub-and-spoke | Any |
| Garbage collection | Easy | Hard (tombstones) |
| Proven implementations | Google Docs, ShareDB | Yjs, Automerge |
| Best for | Server-centric, small docs | P2P, large documents, offline |

## Google Docs Approach (OT)

```
1. Client applies op locally (optimistic update)
2. Client sends op to server with revision number
3. Server transforms op against all intervening ops
4. Server applies and broadcasts transformed op
5. Clients apply server-confirmed ops, transform their pending ops
```

## Modern Recommendation

```
Use Yjs (CRDT) for new systems:
  - Battle-tested (Notion, Figma, Jupyter)
  - Works offline (sync when reconnected)
  - No single point of failure for conflict resolution
  - TypeScript, fast (Rust WASM bindings available)
```
