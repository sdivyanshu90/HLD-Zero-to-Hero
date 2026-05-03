# PACELC Theorem

## Why CAP Is Incomplete

CAP only describes behavior *during network partitions*. But partitions are rare events. What about the other 99.9% of the time when the network is healthy? PACELC extends CAP to cover normal operation as well.

```
PACELC:
  P → Partition?
    A → Availability
    C → Consistency
  E → Else (no partition, normal operation)
    L → Latency
    C → Consistency

Full statement:
  When there IS a partition: choose Availability OR Consistency
  When there IS NO partition: choose Latency OR Consistency
```

---

## The Core Insight: Consistency Always Costs Latency

Even without partitions, achieving strong consistency requires coordination between replicas. Coordination = round trips = latency:

```
Strongly Consistent Write (requires quorum acknowledgment):

  Client ──── write ──────▶ Node A (primary)
                            Node A ──── replicate ──▶ Node B
                            Node A ──── replicate ──▶ Node C
                            Wait for 2/3 ACKs...
                            Node B ◀── ACK ──────────
  Client ◀─── success ────── Node A

  Latency: RTT to primary + replication RTT to replica = 2× network hop

Eventually Consistent Write (fire and forget):
  Client ──── write ──────▶ Node A (primary)
  Client ◀─── success ─────
  Node A replicates to B and C asynchronously (does not block client)

  Latency: 1× network hop
```

---

## PACELC Classification of Systems

```
System         PA/EL    PA/EC    PC/EL    PC/EC
               ──────   ──────   ──────   ──────
               Avail +  Avail +  Consist+ Consist+
               Low Lat  High Con Low Lat  High Con
               ─────────────────────────────────
Cassandra        ✓                          
DynamoDB         ✓       Option            
Riak             ✓                          
PNUTS            ✓                          
Bolt/BigTable    ✓                          
MongoDB                            ✓        
HBase                              ✓        
Postgres                           ✓        
VoltDB                                      ✓
Google Spanner                              ✓
```

### Explanation of Quadrants

```
PA/EL (Partition: Available, Else: Low Latency):
  → Cassandra: stays up during partitions, async replication normally
  → Trade-off: stale reads possible both during and outside partitions
  → Best for: high write throughput, read-heavy workloads tolerating staleness

PA/EC (Partition: Available, Else: Consistent):
  → DynamoDB strong reads: available during partition, synchronous normally
  → You can request strongly consistent reads (costs more latency + money)

PC/EL (Partition: Consistent, Else: Low Latency):
  → PNUTS (Yahoo): refuses writes during partition, but normal ops are fast
  → Niche: needs consistency only during failures, fine with occasional staleness

PC/EC (Partition: Consistent, Else: Consistent):
  → Google Spanner, CockroachDB, VoltDB
  → Never serves stale data, even during partitions or normal operation
  → Costs significant latency (Spanner uses GPS/atomic clocks to minimize)
  → Best for: financial systems, inventory, global ACID transactions
```

---

## Google Spanner: PC/EC in Practice

Spanner achieves PC/EC using TrueTime — a globally synchronized clock with bounded uncertainty:

```
Spanner TrueTime:
  Every Google datacenter has GPS receivers and atomic clocks
  TrueTime API returns: [earliest, latest] — bounded interval of true time

  Commit wait protocol:
    1. Assign commit timestamp T
    2. Wait until TrueTime.now() > T + uncertainty (typically 7ms)
    3. Return success to client

  This ensures all future reads with T' > T see the write
  → External consistency (causal ordering guaranteed globally)

  Cost: ~7ms added to every write (TrueTime uncertainty)
  → This is the minimum latency cost of PC/EC at global scale
```

---

## PACELC in Interview Discussions

When evaluating a database choice, ask:

```
1. What happens during partition?
   → Do I need AP or CP?

2. What are normal-operation latency requirements?
   → Can I afford extra 10ms for quorum writes?
   → Or do I need <1ms (fire-and-forget, eventual)?

3. What staleness is acceptable?
   → Social media feed: seconds of staleness OK
   → Bank balance: zero staleness acceptable
   → Inventory: seconds of staleness → overselling risk

Framework:
  If staleness is unacceptable anywhere → PC/EC (Spanner, CockroachDB)
  If partition availability matters, latency matters → PA/EL (Cassandra)
  If partition availability matters but normal is consistent → PA/EC (DynamoDB strong)
```

---

## Practical Consistency Spectrum

```
←────────── More Consistent ─────────────────── Less Consistent ──────────→
│                                                                            │
│  Linearizable   Serializable   Causal    Read-your-writes   Eventual      │
│                                                                            │
│  Spanner         PostgreSQL     Cassandra  Session           Cassandra     │
│  etcd            MySQL          (causal)   consistency       (async repl)  │
│  CockroachDB     (serializable) MongoDB    DynamoDB          DNS           │
│                  transactions   (causally  (eventual)        social feeds  │
│                                 consistent)                                │
│  Slowest ◄──────────────────────────────────────────────── Fastest        │
```

### Consistency Models Defined

```
Linearizability (strongest):
  Every operation appears to take effect at a single point in real time.
  Operations that return before time T are visible to all operations after T.
  Cost: requires global coordination (Paxos/Raft or TrueTime)

Serializability:
  Concurrent transactions appear to execute in some serial order.
  Allows some reordering as long as result is equivalent to some serial execution.
  PostgreSQL's SERIALIZABLE isolation achieves this.

Causal Consistency:
  Operations that are causally related appear in order to all nodes.
  Operations that are concurrent may appear in different orders at different nodes.
  Cheaper than linearizability; catches most real causality issues.

Read-Your-Writes (Session Consistency):
  A client always reads its own writes.
  Other clients may still see older data.
  Easily achieved: route reads from a session to the node that handled the write.

Eventual Consistency (weakest):
  Given no new writes, all replicas will eventually converge.
  In practice: convergence in milliseconds to seconds.
  No guarantee on how long "eventually" takes.
```

---

## Interview Quick Answers

- **What does PACELC add to CAP?** — CAP only covers behavior during partitions. PACELC adds: even without partitions, you must choose between low latency and consistency. Strong consistency requires coordination (replication confirmation), which adds latency.
- **How does Google Spanner achieve global consistency?** — TrueTime: GPS + atomic clocks with bounded uncertainty. Commit wait: delay commit until TrueTime uncertainty passes (~7ms). This guarantees external consistency globally.
- **What consistency level does Cassandra provide?** — Tunable: from eventual (write to 1 replica) to strong (write to majority). Default is eventual (PA/EL in PACELC terms).
