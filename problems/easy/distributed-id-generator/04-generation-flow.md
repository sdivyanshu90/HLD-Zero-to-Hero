# Step 4 — Generation Flow

## Per-Node ID Generation

```python
import threading, time

class SnowflakeGenerator:
    EPOCH = 1577836800000  # 2020-01-01 UTC ms

    def __init__(self, worker_id: int):
        assert 0 <= worker_id < 1024
        self.worker_id = worker_id
        self.sequence  = 0
        self.last_ms   = -1
        self._lock     = threading.Lock()

    def _current_ms(self) -> int:
        return int(time.time() * 1000)

    def next_id(self) -> int:
        with self._lock:
            now = self._current_ms()

            if now < self.last_ms:          # clock went backward
                raise ClockBackwardError(f"Clock moved back by {self.last_ms - now}ms")

            if now == self.last_ms:
                self.sequence = (self.sequence + 1) & 0xFFF
                if self.sequence == 0:      # sequence exhausted
                    while now <= self.last_ms:
                        now = self._current_ms()  # busy-wait for next ms
            else:
                self.sequence = 0

            self.last_ms = now
            return (
                ((now - self.EPOCH) << 22)
                | (self.worker_id  << 12)
                | self.sequence
            )
```

## Worker ID Assignment

```
Option 1: ZooKeeper sequential ephemeral nodes
  /workers/worker-000001  (auto-assigned sequential ID)
  On connect: create node, extract ID suffix
  On disconnect: node deleted, ID freed

Option 2: etcd lease-based
  worker acquires lease on /workers/{id}
  keeps renewing lease every 5s
  On lease expire: another worker claims same ID

Option 3: Static config
  Each deployment has WORKER_ID env var
  Simple but manual, error-prone

Option 4: IP-based
  hash(IP) % 1024
  Collision risk if many machines; use with caution
```

## High-Level Service Diagram

```
App servers
    │
    │ gRPC / HTTP
    ▼
┌───────────────────────────────┐
│   ID Generator Service        │
│  ┌────────┐  ┌────────┐       │
│  │Worker 0│  │Worker 1│  ...  │
│  └────────┘  └────────┘       │
│        │                      │
│        └── Worker IDs from    │
│            ZooKeeper          │
└───────────────────────────────┘
```

## Batch Generation

```python
def next_ids(self, count: int) -> List[int]:
    """Generate `count` IDs efficiently."""
    ids = []
    for _ in range(count):
        ids.append(self.next_id())
    return ids
```

Clients should batch requests (e.g., 100 IDs per RPC) to reduce round-trips.
