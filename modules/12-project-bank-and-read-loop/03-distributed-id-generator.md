# Cheat Sheet: Distributed ID Generator

## Scale (BoE)
```
Target: 10K-100K IDs/second across all services
Must be: globally unique, sortable by time, no coordination overhead
ID size: 64-bit (fits in BIGINT, safe for most languages/DBs)
```

## Snowflake Layout (Twitter's design)
```
Bit layout (64 bits total):
  [0]        [1-41]           [42-51]        [52-63]
  Sign=0    Milliseconds     Machine ID      Sequence
  1 bit     41 bits          10 bits         12 bits
  (always)  (~69 years)      (1024 machines) (4096 IDs/ms/machine)

Max throughput per machine:
  4096 IDs/ms × 1000 ms/s = 4.096M IDs/second per machine
  
Epoch offset:
  Store (current_ms - custom_epoch) to maximize 41-bit range
  Custom epoch = 2020-01-01 → usable until 2089 (69 years)

Total unique IDs:
  1024 machines × 4096/ms × 86,400,000 ms/day = 363 trillion IDs/day
  Far more than enough for any system
```

## System Diagram
```
Service ──request──▶ ID Generator Node (local/sidecar)
                          │
                     [timestamp_ms - epoch][machine_id][seq++]
                          │
                     return 64-bit ID (no network round trip!)
```

## Key Design Decisions

**1. Machine ID assignment:**
- Hard-coded per deployment (simplest, breaks on scale-out)
- Fetched from ZooKeeper on startup (register machine, get ID)
- **Preferred: etcd or ZooKeeper lease** (machine registers, gets unique 10-bit ID, renews lease)

**2. Clock skew handling:**
- Problem: machine clock goes backward → duplicate IDs!
- Solution: if current_ms < last_ms → wait until clock catches up OR throw exception
- Never assign IDs with timestamp in the past

## Bottlenecks
1. Clock synchronization: NTP drift can cause clock skew → handle gracefully
2. Machine ID exhaustion: only 1024 unique IDs → partition into regions (5 bits region + 5 bits machine)

## Unique Trick
No central coordination needed — each machine generates IDs independently. Time-sortable because timestamp is the high bits. The entire generator fits in ~50 lines of code per machine.
