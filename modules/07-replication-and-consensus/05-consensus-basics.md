# Consensus Algorithms: Paxos and Raft

## The Consensus Problem

Consensus: getting multiple nodes to agree on a single value, even in the presence of node failures and network partitions.

```
Why is consensus hard?

Scenario:
  3 nodes need to agree on "who is the primary?"
  
  Node A says: "I am the primary" (sends message to B and C)
  Node B says: "I am the primary" (sends message to A and C)
  Node C receives both messages → which to accept?
  
  If messages are delayed or lost → nodes may make different decisions
  → Some nodes commit value V, others commit value V'
  → SAFETY VIOLATION (inconsistency)

Consensus guarantees:
  1. Agreement: all non-faulty nodes decide the same value
  2. Validity: the decided value was proposed by some node
  3. Termination: all non-faulty nodes eventually decide
  4. Integrity: no node decides twice
```

---

## Paxos

Original consensus algorithm by Leslie Lamport (1989/1998). The basis for almost all production consensus:

```
Roles:
  Proposers: propose a value (want to be elected leader)
  Acceptors: vote on proposals (quorum required)
  Learners: learn the agreed-upon value

Phase 1 (Prepare):
  Proposer P sends: PREPARE(n) to all acceptors
  (n = ballot number, must be unique and monotonically increasing)
  
  Acceptors respond:
    If n > any ballot previously seen:
      PROMISE(n, v_last, n_last)  ← "I promise not to accept < n"
      Include the last accepted value (if any)
    Else:
      NACK (already promised to a higher ballot)

Phase 2 (Accept):
  P receives PROMISE from majority of acceptors
  If any PROMISE included a previous accepted value:
    → P MUST use that value (not its own!) — crucial for safety
  Else:
    → P can use its own proposed value
  
  P sends: ACCEPT(n, value) to all acceptors
  
  Acceptors: if n >= promised ballot → accept value, send ACCEPTED(n) to learners
  
  Learners: value is committed once a majority send ACCEPTED(n)
```

### Paxos In Action: Leader Election

```
5 nodes: N1, N2, N3, N4, N5

N1 wants to become leader:
  Phase 1: N1 sends PREPARE(n=10) to all 5 nodes
  Responses:
    N2: PROMISE(10, null, null)  ← hasn't accepted any value yet
    N3: PROMISE(10, null, null)
    N4: PROMISE(10, null, null)
    N5: PROMISE(10, null, null)
    N1: (self) PROMISE
  Majority (3/5) achieved!

  Phase 2: N1 sends ACCEPT(n=10, value="N1 is leader")
  Responses: N2, N3, N4 send ACCEPTED(10) to all learners
  Majority (3/5) achieved!
  
  Consensus: "N1 is leader" with epoch 10

  If N3 crashes between Phase 1 and Phase 2:
    Phase 2 still succeeds (N2, N4, N5 form majority)
    N3 will catch up when it recovers
```

### Multi-Paxos (Repeated Consensus)

```
Basic Paxos: one round = one decision (expensive!)
Multi-Paxos optimization: amortize Phase 1 across many rounds
  Once a leader is established with epoch n:
    Skip Phase 1 for all future rounds (use same n)
    Only run Phase 2 for each new log entry
  → ~1 RTT per log entry in steady state (leader to majority + reply)

This is basically how Raft works (just more clearly specified)
```

---

## Raft

Raft was designed to be more understandable than Paxos (Diego Ongaro & John Ousterhout, 2014). It is now the dominant consensus algorithm in new systems:

```
State machine:
  Each server is in one of: FOLLOWER, CANDIDATE, LEADER

  ┌─────────────────────────────────────────────────────────────┐
  │  FOLLOWER                                                    │
  │  - Passive: responds to RPCs from leader and candidates      │
  │  - Resets election timeout on each heartbeat                 │
  │  - If no heartbeat: converts to CANDIDATE                    │
  └─────────────────────────────────────────────────────────────┘
              │ election timeout (150-300ms) elapses
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  CANDIDATE                                                   │
  │  - Increments term, votes for itself                         │
  │  - Sends RequestVote RPCs to all other nodes                 │
  │  - If majority votes: becomes LEADER                         │
  │  - If another leader appears: reverts to FOLLOWER            │
  │  - If timeout: start new election                            │
  └─────────────────────────────────────────────────────────────┘
              │ receives majority votes
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  LEADER                                                      │
  │  - Sends heartbeats to all followers (AppendEntries RPC)     │
  │  - Handles all client requests                               │
  │  - Replicates log entries to followers                       │
  │  - Commits entry once majority ACK it                        │
  └─────────────────────────────────────────────────────────────┘
```

### Raft Log Replication

```
Client request: "Set x = 5"

1. Client sends to LEADER (or redirected to leader)
2. Leader appends to its log: [index=42, term=3, cmd="set x=5"]
3. Leader sends AppendEntries RPC to all followers:
   {term:3, prevLogIndex:41, prevLogTerm:3, entries:[{42,3,"set x=5"}], leaderCommit:41}
4. Followers append to their logs, reply OK
5. Once majority (3/5) reply OK:
   Leader commits the entry (applies to state machine)
   Leader responds to client: "OK"
6. Next heartbeat: leaderCommit=42 → followers apply entry 42

Safety:
  Raft ensures: if an entry is committed at index i, NO future leader
  will commit a different entry at index i
  → Proof: election requires majority; new leader must have all committed entries
           (RequestVote rejected if candidate log is less up-to-date)
```

---

## Where Consensus Is Used

```
System           Consensus Use                    Algorithm
──────────────────────────────────────────────────────────────────
ZooKeeper        Distributed coordination, locks  ZAB (Zookeeper Atomic Broadcast)
etcd             Kubernetes cluster state          Raft
Consul           Service discovery, config         Raft
CockroachDB      Distributed transactions          Raft (per-range)
TiKV             Distributed KV store             Raft (multi-raft)
Kafka            Controller election               ZooKeeper (migrating to KRaft)
Redis Sentinel   Leader election for failover      Raft-like
Google Chubby    Distributed locking               Paxos
Spanner          Global transaction ordering       Paxos groups
```

---

## Consensus vs Replication

```
Replication (async or semi-sync):
  Fast: leader doesn't wait for all replicas
  Not strictly consistent: replicas may have different data at any moment
  Leader failure: may lose recent uncommitted writes

Consensus-based replication:
  Strict: entry committed only when majority ACK
  Any committed entry guaranteed to be on any future leader
  → Zero RPO for committed writes
  
  Cost: 1+ RTT per commit (leader to majority of quorum)
  For 3-node cluster, same AZ: ~0.5ms overhead per write
  For geo-distributed 5-node cluster: ~50-100ms per write (cross-region RTT)
```

---

## Interview Quick Answers

- **What is the key difference between Raft and Paxos?** — Both achieve the same result (consensus), but Raft is decomposed into clear subproblems (leader election, log replication, safety) and is significantly easier to understand and implement correctly. Paxos is more flexible but notoriously hard to implement without subtle bugs.
- **What happens during a Raft leader election?** — A follower whose election timeout elapses becomes a candidate, increments its term, votes for itself, and sends RequestVote RPCs. A candidate wins if it gets votes from a majority of nodes. A node grants a vote only if the candidate's log is at least as up-to-date as its own (prevents electing a stale node).
- **Why does consensus require a majority (not any N replicas)?** — Two majorities of N nodes must overlap by at least 1 node. That overlap node ensures any new majority (e.g., new leader) has seen what any previous majority (e.g., old leader's commit) decided. This prevents two conflicting values from being committed.
