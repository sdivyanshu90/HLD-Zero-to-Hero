# Step 5 — Clock Skew and Sequence Handling

## Problem: NTP Clock Adjustments

```
Server time:
  t=100ms → t=101ms → t=99ms  ← NTP stepped back 2ms

If we generate IDs at t=100, t=101, then t=99:
  ID at t=99 < ID at t=100  → NOT monotonic → sortability broken
```

## Strategies for Clock Going Backward

### Strategy 1: Reject (fail fast)

```python
if now < self.last_ms:
    raise ClockBackwardError(...)
```
Safest. Service returns error; client retries (hoping clock is corrected).

### Strategy 2: Wait until caught up

```python
if now < self.last_ms:
    delta = self.last_ms - now
    if delta <= 5:          # tolerate up to 5ms
        time.sleep(delta / 1000.0)
        now = self._current_ms()
    else:
        raise ClockBackwardError(f"Excessive skew: {delta}ms")
```

### Strategy 3: Use last known good timestamp

```python
if now < self.last_ms:
    now = self.last_ms  # pretend it's still last_ms
    # sequence will overflow quickly → waits for next ms anyway
```

## Sequence Overflow

```
If 4096 IDs are generated within 1 ms:
  sequence wraps to 0
  generator busy-waits for next millisecond

Estimated wait: < 1 ms
At 4096 IDs/ms we're already at the hardware limit per node
→ scale horizontally (add worker nodes)
```

## NTP Best Practices

```
1. Use chrony or systemd-timesyncd instead of ntpd
   → smaller, smoother adjustments (slews, not steps)
2. Disable time stepping in production:
   makestep 0.1 3   # only step if > 0.1s off, max 3 times at boot
3. Monitor clock offset: Prometheus node_exporter exposes NTP offset
4. Alert if offset > 10ms
```

## Sequence Reset Strategy

```
On new millisecond: reset seq to 0
On restart: reset seq to 0 (first ms may regenerate seq 0 again,
  but ts portion increases so full ID is still unique)

Risk: Two nodes with same worker_id running simultaneously
Fix: ZooKeeper / etcd ensures at-most-one active lease per worker_id
```

## Summary of Clock Skew Mitigations

```
┌────────────────────────────────────────────────────────────┐
│  Clock went backward by:                                   │
│   < 5 ms   → wait (spin)                                   │
│   5-100 ms → wait with backoff + alert                     │
│   > 100 ms → reject; escalate to ops                       │
│                                                            │
│  Monotonicity within a node: guaranteed by mutex + last_ms │
│  Monotonicity across nodes:  approximate (ts alignment)    │
└────────────────────────────────────────────────────────────┘
```
