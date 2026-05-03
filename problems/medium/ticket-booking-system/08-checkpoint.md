# Step 8 — Checkpoint & Interview Q&A

**Q1: How do you prevent double-booking when 100K users hit "book" simultaneously?**
> Use Redis SET NX (set if not exists) as the first lock. Only one user gets `SET seat:123 user_456 NX EX 600` to return success — the others get nil. The winner then writes to the DB in a transaction. This serializes competing requests in memory before touching the database.

**Q2: Why 10-minute hold instead of immediately booking?**
> Payment processing takes 3-10 seconds. If we book first and payment fails, the seat is permanently lost. The hold pattern: (1) reserve seat atomically, (2) process payment within hold window, (3) confirm booking on payment success, (4) auto-release hold on payment failure or timeout.

**Q3: How do you handle a flash sale where 100K users compete for 100 seats?**
> Multi-tier filtering: (1) IP/user rate limiting at API gateway to reduce 100K to ~10K req/sec. (2) Redis atomic counter `DECR available_count` — only first 100 get through (99,900 get 429). (3) Individual seat lock via Redis NX for the 100 winners. (4) DB transaction to confirm. Only 100 DB writes, not 100K.

**Q4: What happens if the Redis hold expires before payment completes?**
> On TTL expiry, the seat becomes available again. The next user could acquire the hold. If the original user's payment eventually succeeds, the DB write would fail (seat status != HELD for their user_id). The booking service detects this and either apologizes + refunds, or attempts to re-hold if still available.

**Q5: How do you show real-time seat availability to users?**
> Seat map is cached in Redis as a bitmap or hash (seat_id → status). Long-polling or WebSocket streams availability changes. On each hold/release, publish to a Redis channel that seat viewers subscribe to. Avoid reading DB directly — too slow for thousands of concurrent seat map viewers.
