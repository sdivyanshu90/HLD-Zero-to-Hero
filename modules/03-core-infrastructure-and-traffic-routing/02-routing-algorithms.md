# Load Balancing Routing Algorithms

## The Core Problem

When distributing requests across N backends, which backend gets each request? Different algorithms optimize for different goals: even distribution, latency, stateful affinity, or capacity-aware routing.

---

## Round Robin

The simplest algorithm. Requests go to backends 1, 2, 3, 1, 2, 3, ... in sequence:

```
Round Robin:
  Request 1 → Server A
  Request 2 → Server B
  Request 3 → Server C
  Request 4 → Server A  (back to start)
  ...

Pros: Simple, even distribution assuming equal request cost
Cons: Ignores server capacity differences, ignores request duration
      Server A with 10 long requests = same treatment as Server B with 10 fast requests
```

### Weighted Round Robin

Assigns more requests to higher-capacity servers:

```
Server A: weight=3 (powerful machine)
Server B: weight=2
Server C: weight=1

Sequence: A, A, A, B, B, C, A, A, A, B, B, C, ...
→ Server A gets 3× the requests of Server C
```

---

## Least Connections

Routes to the backend with the fewest active connections:

```
Current state:
  Server A: 10 active connections
  Server B: 5 active connections   ← next request goes here
  Server C: 8 active connections

Next request → Server B

Pros: Handles varying request durations better than round robin
Cons: Connection count ≠ server load (a server with 5 heavy requests may be
      more loaded than one with 10 lightweight requests)

Used by: AWS ALB (least outstanding requests variant)
         Nginx upstream (least_conn directive)
```

### Least Response Time

Routes to the backend with the lowest combination of active connections AND response time:

```
Score = active_connections × avg_response_time

Server A: 5 connections × 50ms = 250
Server B: 2 connections × 200ms = 400  ← despite fewer connections, higher score
Server C: 3 connections × 60ms = 180   ← lowest score → pick this one

Pros: Best latency optimization
Cons: Requires tracking response time (more complex)
Used by: HAProxy, Nginx Plus
```

---

## IP Hash (Sticky Routing)

Routes based on hash of client's IP address. Same client always goes to same server:

```
Hash(client_ip) % num_servers = server index

Client 203.0.113.5  → Hash → 2 → Server C  (always!)
Client 198.51.100.1 → Hash → 0 → Server A  (always!)

Pros: Stateful clients always reach the same server
Cons: If server C dies, all its clients must rehash → may not land on same server
      IP hash changes when adding/removing servers (use consistent hashing instead)
```

---

## Consistent Hashing

Maps both clients and servers to positions on a virtual ring. A client is always routed to the first server clockwise from its position on the ring:

```
Virtual Ring (0 to 2^32):

        Server B (pos: 512)
             │
   0 ────────┤──────────────── 1024 ──── 2048
             │        │              │
         Client X  Server A       Server C
         (pos:800) (pos:1100)     (pos:2500)

Client X (800) → clockwise → Server A (1100)
If Server A is removed: Client X → clockwise → Server C (2500)
Only clients between Server B and Server A are affected!

Without consistent hashing (simple hash mod N):
  Remove 1 server → all N-1 hashes change → massive cache invalidation!
With consistent hashing:
  Remove 1 server → only 1/N of keys need to move
```

Virtual nodes (vnodes) improve balance:

```
Each physical server maps to 100-200 virtual ring positions:

Ring: ...──[A1]──[B1]──[A2]──[C1]──[B2]──[A3]──[C2]──...
             Server A = A1, A2, A3 positions

Benefits:
  - Even distribution even with heterogeneous server counts
  - When server fails, its load spreads across ALL remaining servers
    (not just its two neighbors on the ring)
```

---

## Random with Two Choices (Power of Two Choices)

Pick 2 random backends, send to the less loaded one:

```
Algorithm:
  1. Pick server X at random
  2. Pick server Y at random  
  3. Compare load(X) vs load(Y)
  4. Route to whichever has lower load

This approximates "least loaded" with O(1) work
No need to maintain global state

Theoretical result:
  N random requests among N servers:
    Naive random: max load = O(log N / log log N)
    Power of two: max load = O(log log N)
    → Exponential improvement in worst-case load imbalance
```

---

## Algorithm Comparison

| Algorithm | Complexity | State Needed | Best For |
|-----------|------------|--------------|----------|
| Round Robin | O(1) | Counter | Equal-cost stateless requests |
| Weighted Round Robin | O(1) | Weights + counter | Heterogeneous server capacity |
| Least Connections | O(1) | Active connection count | Variable request duration |
| Least Response Time | O(1) | Response time + conn count | Latency-sensitive services |
| IP Hash | O(1) | Hash function | Session affinity (with caveats) |
| Consistent Hash | O(log N) | Ring data structure | Cache affinity, key-based routing |
| Power of Two | O(1) | Per-server load count | High-scale, balanced distribution |

---

## Real-World Usage

```
AWS ALB:         Least Outstanding Requests (default) or Round Robin
GCP Load Balancer: Round Robin with Utilization fallback
Nginx:           Round Robin (default), Least Connections, IP Hash, random
HAProxy:         Round Robin, Least Connections, Source Hash, URI Hash
Envoy Proxy:     Round Robin, Least Request, Random, Ring Hash, Maglev Hash
Kubernetes:      Round Robin (kube-proxy) or consistent hash (IPVS mode)
Redis Cluster:   16,384 hash slots (consistent partitioning variant)
Cassandra:       Virtual node consistent hashing
```

---

## Interview Quick Answers

- **Why use consistent hashing over modular hashing for distributed caches?** — Adding/removing a node in modular hashing invalidates O(N) cache entries. Consistent hashing only moves O(1/N) entries — dramatically less cache churn.
- **What is the power-of-two-choices algorithm?** — Pick 2 random servers; route to the less loaded one. Achieves near-optimal balance without a centralized global state.
- **When does round robin fail?** — When requests have very different durations. A long upload to Server A blocks it while Server B and C get many short requests — Server A's connection count looks low.
