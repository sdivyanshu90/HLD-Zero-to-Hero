# Step 8 — Checkpoint & Interview Q&A

**Q1: How do you crawl 1 B URLs in 30 days?**
> Math: 1 B URLs / (30 × 86400) ≈ 385 URLs/sec. If each fetcher handles 10 URLs/sec (accounting for network + politeness delays), need 39 fetchers. In practice, use 100-200 fetcher machines for headroom. URL frontier distributed across Kafka partitions — each fetcher consumes from assigned partitions.

**Q2: How do you avoid re-crawling the same URL?**
> Bloom filter: 1 GB memory, 0.1% false positive rate, 1 B URL capacity. Before adding a URL to the frontier, check the bloom filter. If "probably seen" → skip. FP rate means we occasionally skip a URL we haven't seen — acceptable. On full re-crawl (monthly), rebuild bloom filter from scratch.

**Q3: How do you respect robots.txt at scale?**
> Cache robots.txt per domain in Redis (TTL 24h). Before crawling any URL, fetch the domain's cached robots rules and check the URL path against Disallow rules. Crawl-delay directive is enforced per domain via a per-domain rate limiter (one queue per domain, delay between dequeues).

**Q4: How do you prioritize which URLs to crawl first?**
> Two-level frontier: Priority queue (Kafka topic priority) — based on PageRank estimate, freshness signals, domain importance. Politeness queue — per domain FIFO with rate limiting. High-priority pages (news, high-PR domains) get into the next crawl wave first. Low-priority (obscure blogs) may wait days.

**Q5: How do you detect and handle spider traps?**
> Spider traps are infinite URL generators (e.g., calendars with infinite "next month" links). Detections: (1) URL depth limit (> 20 hops from seed → skip). (2) Path repetition detection (same segment repeated 3+ times). (3) Per-domain URL count limit (> 100K URLs per domain → flag for review). (4) URL length limit (> 500 chars → skip).
