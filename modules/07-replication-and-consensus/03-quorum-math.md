# Quorum Math

## The Core Equation

For a distributed system to provide strong consistency with N replicas:

```
Strong consistency: W + R > N

Where:
  N = total replica count (replication factor)
  W = minimum replicas that must ACK a write
  R = minimum replicas that must respond to a read

Intuition:
  If W nodes confirmed the write, and R nodes respond to the read,
  then at least (W + R - N) nodes participated in BOTH operations
  → At least one node has the latest value
  → Return the highest-versioned value among R responses
```

---

## Quorum Configurations

```
N=3 replication factor:
  
  Config          W   R   W+R   Consistent?  Write     Read
                                             Avail.    Avail.
  ──────────────────────────────────────────────────────────
  QUORUM/QUORUM   2   2    4>3  ✓ YES        Good      Good
  ALL/ONE         3   1    4>3  ✓ YES        Poor      Excellent
  ONE/ALL         1   3    4>3  ✓ YES        Excellent Poor
  ONE/ONE         1   1    2<3  ✗ NO         Excellent Excellent
  ONE/QUORUM      1   2    3=3  ✗ NO (edge)  Excellent Good
  ALL/ALL         3   3    6>3  ✓ YES        Poor      Poor
```

---

## Quorum and Node Failures

```
N=3 cluster, W=2, R=2 (QUORUM configuration):

  One node fails:
    Write: 2 nodes available, W=2 → write SUCCEEDS (2/2 nodes respond)
    Read:  2 nodes available, R=2 → read SUCCEEDS (2/2 nodes respond)
    Cluster is fully operational with 1 failure!

  Two nodes fail:
    Write: 1 node available, W=2 → write FAILS (cannot reach quorum)
    Read:  1 node available, R=2 → read FAILS (cannot reach quorum)
    Cluster is unavailable until a second node recovers.

  Rule: with QUORUM configuration on N nodes:
    Can tolerate floor(N/2) node failures and stay available
    floor(3/2) = 1 failure
    floor(5/2) = 2 failures
    floor(7/2) = 3 failures
```

---

## Cassandra Consistency Levels

```
Cassandra quorum levels (N = replication factor in keyspace):

  ONE:          W=1, R=1  → fastest, eventual consistency
  TWO:          W=2, R=2  → for N>=3, stronger but slower
  THREE:        W=3, R=3  → very strong, very slow
  QUORUM:       W=ceil(N/2)+1, R=ceil(N/2)+1  → strong with majority
  LOCAL_QUORUM: quorum within local datacenter only  → geo-aware
  EACH_QUORUM:  quorum in EACH datacenter  → very strong, cross-DC
  ALL:          W=N, R=N  → maximum durability/consistency, lowest availability
  LOCAL_ONE:    W=1 in local DC, R=1 in local DC  → fastest, eventual

Production recommendation:
  Write: LOCAL_QUORUM (2/3 in local DC + async to remote DC)
  Read:  LOCAL_QUORUM (read from 2/3, return latest)
  → Strong consistency within a DC, eventual across DCs
  → Continues operating if 1 local node fails
```

---

## Read Repair and Anti-Entropy

Quorum reads may reveal stale data on some replicas. How to fix them:

```
Read Repair (Cassandra):
  Client reads key X with QUORUM:
    Node A returns {x: 5, ts: 1000}
    Node B returns {x: 5, ts: 1000}
    Node C returns {x: 3, ts: 800}   ← stale!
  
  Coordinator notices C is stale
  Repair options:
    Synchronous (read_repair = BLOCKING): update C before returning to client
    Asynchronous (read_repair = BACKGROUND, default): return result immediately,
      repair C in background
  
  Client always receives the latest value (ts: 1000, x: 5)

Merkle Trees for Anti-Entropy:
  Background process compares data between replicas
  Builds a Merkle tree (hash tree) for each replica:
    Leaf nodes: hash(row)
    Internal nodes: hash(children)
    Root: hash of entire data range
  
  Compare roots: if equal → no diff, skip
  If different: binary search to find which subtree differs → sync only different leaves
  
  Efficient: only detect differences without transmitting all data
  Cassandra's "repair" command uses Merkle trees
  Used also by DynamoDB, Riak, Dynamo-family systems
```

---

## Sloppy Quorum and Hinted Handoff

```
Strict quorum: write must be confirmed by the N "home" nodes for that key
  → If 2 home nodes are down: writes fail (can't reach W=2)

Sloppy quorum: write goes to any W nodes available (not necessarily home nodes)
  → Even if home nodes are down: write still succeeds!
  → The "hint" is stored on the surrogate node:
     "This write for partition X should go to Node C when it comes back"

Hinted Handoff:
  Node C comes back online
  Surrogate node delivers all hints to Node C
  Node C replays them and becomes fully caught up

  Amazon Dynamo uses sloppy quorum + hinted handoff
  Cassandra uses hinted handoff for temporary node failures
  Hint stores: deleted after hint_window_persistent_total_size_in_mb or hint expires

  Trade-off:
    ✓ Higher write availability (W out of any available nodes)
    ✗ Reads during the outage may miss the hinted writes (stale reads)
    ✗ Hints can accumulate: if hint_window expires and C never comes back,
      Node C permanently misses those writes → repair needed on recovery
```

---

## Interview Quick Answers

- **How many nodes can fail in a Cassandra 5-node cluster with QUORUM reads and writes?** — W=3, R=3 (ceil(5/2)+1 = 3). A node fails, leaving 4. W+R=6>5 still holds with 4 nodes, since min(available, W)=3 is achievable. Can tolerate `floor(5/2)=2` failures and maintain QUORUM.
- **What is the difference between sloppy quorum and strict quorum?** — Strict quorum: the write/read must involve the specific "home" nodes for that key. Sloppy quorum: any available nodes can serve, with hinted handoff delivering writes to home nodes later. Sloppy quorum improves availability at the cost of potentially returning stale reads during node outages.
- **Why does W+R > N guarantee strong consistency?** — If W nodes confirmed the write, and R nodes respond to a read, then at least W+R-N nodes participated in both. That overlap guarantees at least one node has the latest write. Returning the highest-versioned value from R responses always gives the most recent value.
