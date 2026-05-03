# Step 8 — Checkpoint & Interview Q&A

## Core Questions

**Q1: How do you ensure short code uniqueness?**
> Use random base62 generation with a bloom filter for fast negative checks, backed by a DB unique constraint as the final arbiter. At > 10K writes/sec, switch to a pre-generated key table (KGS) with range-based allocation to avoid lock contention.

**Q2: 301 vs 302 redirect — which do you choose and why?**
> 302 for analytics-heavy use cases (every redirect is counted server-side). 301 for performance-first (browser caches, lower server load). Production systems often expose a config per-link.

**Q3: How does the cache handle a popular URL that just expired?**
> Three mitigations: (1) TTL jitter prevents mass simultaneous expiry, (2) Redis mutex pattern serialises the first re-fetch, (3) background refresh proactively updates entries before they expire.

**Q4: How would you scale this to 10× traffic?**
> Redirect Service: add pods (stateless). Redis: cluster mode with 6 shards. MySQL: add read replicas. Key Gen: pre-allocated ranges per write server. CDN: push 301 responses to edge for top URLs.

**Q5: How would you add click analytics without impacting redirect latency?**
> Redirect Service publishes a lightweight click event to Kafka (fire-and-forget, < 1 ms). A downstream Flink/Kafka Streams job aggregates and writes to a separate analytics DB (ClickHouse/TimescaleDB). Main redirect path never touches analytics DB.

**Q6: What happens when the MySQL primary fails?**
> Reads continue from replicas. Writes queue in an async buffer (Kafka) or return 503. Replica is promoted to primary (seconds with automated failover via ProxySQL/PgBouncer/Aurora). Eventual consistency on click counts during failover window.

## Design Variants

| Variant | Change |
|---------|--------|
| Multi-region | Geo-route DNS; replicate DB to each region; accept stale reads |
| Link preview | HEAD request on creation; store og:title + og:image |
| QR code | Generate QR on-the-fly from short_url using qrcode lib |
| Abuse detection | ML model on long_url domain; block known phishing domains |

## Self-Assessment Rubric

- [ ] Can explain write path end-to-end in < 2 minutes
- [ ] Can explain redirect path and cache tiers
- [ ] Can calculate BoE numbers from scratch
- [ ] Can articulate 3 failure modes and mitigations
- [ ] Know 301 vs 302 trade-off cold
