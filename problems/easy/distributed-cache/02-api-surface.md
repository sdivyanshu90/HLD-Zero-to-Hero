# Step 2 — API Surface

## Core Operations

```python
class CacheClient:
    def get(self, key: str) -> Optional[bytes]:
        """Return value or None if missing / expired."""

    def set(self, key: str, value: bytes,
            ttl_seconds: Optional[int] = None) -> None:
        """Store key-value. Evicts LRU entry if at capacity."""

    def delete(self, key: str) -> bool:
        """Remove key. Returns True if existed."""

    def exists(self, key: str) -> bool:
        """Check membership without resetting LRU order."""

    def mget(self, keys: List[str]) -> List[Optional[bytes]]:
        """Batch get — reduces round-trips."""

    def mset(self, items: Dict[str, bytes],
             ttl_seconds: Optional[int] = None) -> None:
        """Batch set."""
```

## Wire Protocol (Redis-compatible RESP)

```
SET mykey myvalue EX 300
*4\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$7\r\nmyvalue\r\n$3\r\nEX\r\n

GET mykey
*2\r\n$3\r\nGET\r\n$5\r\nmykey\r\n
```

## Node Selection (Client-Side)

```python
def get_node(key: str, nodes: List[Node]) -> Node:
    ring = ConsistentHashRing(nodes, virtual_nodes=150)
    return ring.get_node(key)
```

## Error Handling

| Error | Client Behaviour |
|-------|-----------------|
| Node unreachable | Mark node down; reroute to next node on ring |
| Network timeout | Retry once with 2ms deadline; else return None |
| OOM on SET | Node evicts LRU entry; SET proceeds |
| Invalid key (too long) | Client-side validation before sending |
