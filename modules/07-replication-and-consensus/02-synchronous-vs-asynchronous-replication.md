# Synchronous vs Asynchronous Replication

## The Durability-Availability Trade-off

```
Synchronous (sync) replication:
  Primary waits for at least one replica to confirm BEFORE ACKing the client
  
  Client ──▶ Primary ──▶ Replica 1 (sync)
                    └──▶ Replica 2 (async)
  
  Primary ACKs client only after Replica 1 confirms
  → If Primary fails, Replica 1 has ALL committed data → no data loss

Asynchronous (async) replication:
  Primary ACKs client immediately, replicates in background
  
  Client ──▶ Primary ──ACK──▶ Client
                │
                └── (background) ──▶ Replica 1
                                 └──▶ Replica 2
  
  → If Primary fails before replicating: some committed writes may be LOST
  → But Primary is not blocked on replica latency → better write throughput
```

---

## Semi-Synchronous Replication (The Real-World Sweet Spot)

```
Semi-synchronous: 1 sync replica, rest async (MySQL default for group replication)

Primary ACK flow:
  Client ──▶ Primary:
    1. Write to WAL
    2. Replicate to Replica 1 (sync) — wait for ACK
    3. ACK client ("committed!")
    4. Replicate to Replica 2, 3, ... (async, in background)

  Why this works:
    No data loss on PRIMARY failure (Replica 1 has all data)
    Tolerable latency overhead (~1 RTT extra = 0.5ms same-AZ, 5ms cross-AZ)
    Write throughput not blocked by slow Replica 2/3
```

---

## Replication Modes in Practice

```
PostgreSQL synchronous_standby_names:
  FIRST 1 (replica1, replica2)   # wait for FIRST 1 of these
  ANY 2 (replica1, replica2, replica3)   # wait for ANY 2 of these

MySQL binlog:
  sync_binlog=1: sync binlog to disk on every commit (durable)
  rpl_semi_sync_master_enabled=ON: semi-sync replication

Cassandra write path:
  QUORUM: wait for ceil(N/2)+1 replica ACKs before returning success
  ALL: wait for ALL N replicas
  ONE: write to just 1 replica, return immediately

  QUORUM in 3-node cluster: wait for 2 ACKs
  → One replica can be down and writes still succeed
  → RPO (Recovery Point Objective) = 0 (no data loss on single failure)
```

---

## Replication Lag Metrics and Monitoring

```
How to measure replication lag:
  PostgreSQL:
    SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
    → Returns lag in seconds
    
    SELECT client_addr, write_lag, flush_lag, replay_lag 
    FROM pg_stat_replication;
    → Per-replica lag at different stages

  MySQL:
    SHOW SLAVE STATUS\G;
    → Seconds_Behind_Master: seconds

  Cassandra:
    nodetool tpstats | grep Mutations
    → Pending mutations queue size per node

Alert thresholds (typical production):
  Warning:  > 1 second lag (stale reads becoming noticeable)
  Critical: > 10 seconds lag (significant staleness risk)
  Emergency: > 60 seconds lag (operations problem, failover risk)
```

---

## RPO and RTO

```
Recovery Point Objective (RPO):
  Maximum data loss acceptable after a failure
  "How much data can we afford to lose?"
  
  Async replication: RPO = replication lag (seconds to minutes)
  Sync replication: RPO = 0 (no data loss)
  
  Financial systems: RPO = 0 (cannot lose a single transaction)
  Social media feed: RPO = 60s (a few lost likes is acceptable)

Recovery Time Objective (RTO):
  Maximum downtime acceptable after a failure
  "How quickly must we recover?"
  
  Cold standby: RTO = hours (boot up standby, restore data)
  Warm standby: RTO = minutes (standby running, catch up from WAL)
  Hot standby: RTO = seconds (standby already in sync, auto-failover)
  Active-active: RTO = 0 (other nodes immediately take over, no election)

Trade-off:
  Lower RPO → sync replication → higher write latency
  Lower RTO → hot standby or active-active → higher operational complexity
```

---

## Failover Automation

```
PostgreSQL Patroni (most popular automated HA):
  Patroni: Python daemon running on each PostgreSQL node
  Stores cluster state in etcd/Consul/ZooKeeper
  
  Normal:
    Primary: Patroni writes its leadership lease to etcd every ~10s
    Replica: watches etcd for primary's lease
  
  Primary fails:
    1. etcd lease expires (10s after last heartbeat)
    2. Replicas notice leader gone
    3. Election: whichever replica acquires the etcd leadership key first wins
    4. Winner: runs pg_ctl promote → becomes new primary
    5. Other replicas: repoint to new primary's WAL stream
    6. HAProxy: health checks detect new primary, routes writes there
  
  Total failover time: ~30 seconds (lease timeout + election + promotion)
  
  Split-brain prevention:
    Only one node can hold etcd leadership key at once (etcd is CP)
    Old primary, if it comes back, will see it doesn't hold the key → stays replica
```

---

## Interview Quick Answers

- **What is synchronous replication and what does it cost?** — The primary waits for replica(s) to confirm before ACKing the client. Guarantees zero data loss on primary failure. Cost: added latency equal to one replication round trip (~0.5ms same-AZ, ~5ms cross-AZ, ~50-100ms cross-region).
- **What is semi-synchronous replication?** — One replica is synchronous (primary waits for it), others are async. Guarantees zero data loss (sync replica always current), but doesn't block on slow async replicas. Best of both worlds for most production systems.
- **What is RPO vs RTO?** — RPO = max data loss (how old can the data be on recovery). RTO = max downtime (how long to recover). Lower RPO requires sync replication. Lower RTO requires hot standbys with automated failover.
