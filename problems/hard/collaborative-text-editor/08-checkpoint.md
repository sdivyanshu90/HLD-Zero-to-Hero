# Step 8 — Checkpoint & Interview Q&A

**Q1: What's the difference between OT and CRDT?**
> OT transforms the position of each operation based on concurrent operations — it needs a central server to determine operation ordering. CRDT assigns a globally unique ID to each character so operations commute (can be applied in any order). OT is simpler in memory but requires a central arbiter; CRDT supports P2P/offline but has high memory overhead (40× for text due to per-character IDs and tombstones).

**Q2: How do you handle a user going offline and making edits, then reconnecting?**
> With CRDT: all offline edits are buffered locally. On reconnect, the client sends all buffered operations (with their CRDT IDs). The server (or other peers) applies them in any order — CRDT guarantees the same final state regardless of order. With OT: offline edits include the last-seen revision number. On reconnect, the server transforms the batch of ops against all intervening ops since that revision.

**Q3: How do you implement cursor position sharing in real-time?**
> Cursor positions are not part of the document state — they're ephemeral presence data. Each client broadcasts `{user_id, position}` via WebSocket to all other collaborators in the same document session. Positions are stored in Redis (TTL 30s, refreshed with each cursor move). No persistence needed — lost on disconnect.

**Q4: How do you scale a document that has 1000 simultaneous editors?**
> Session Server becomes a bottleneck. Shard document sessions across servers. Use Redis Pub/Sub to route operations between session servers. For extremely hot documents (> 500 editors), use a hierarchical fan-out: document server → region proxies → clients. Consider read replicas that don't need to process incoming ops (read-only viewers).

**Q5: How do you persist the document state without writing every keystroke to a database?**
> Two-tier persistence: (1) Operation log — every operation appended to Kafka (durable). (2) Snapshot store — full document state written to DB every N operations or every 60 seconds (whichever comes first). On reload: fetch latest snapshot, replay operations since snapshot. This is similar to Kafka's offset-based recovery model.
