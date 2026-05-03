# Step 8 — Checkpoint & Interview Q&A

**Q1: Why pre-compute top-K at every trie node instead of computing on query?**
> Computing top-K from leaves at query time is O(N) where N is the subtree size — potentially millions of nodes for a single-character prefix. Pre-computing stores the top-K list at each node, making query time O(1) (a single Redis GET). The trade-off is higher storage (10M keys × 500B = 5 GB) and rebuild time, but it's the only way to meet < 50ms SLA at scale.

**Q2: How do you handle a new trending term (e.g., "ChatGPT") appearing in autocomplete?**
> Two-tier update strategy: (1) Batch rebuild (nightly): updates all prefix top-K based on last 7 days of search logs — latency 24 hours. (2) Incremental update (every 10 min): Count-Min Sketch tracks approximate term frequency in real-time; hot terms update their prefix entries in Redis. Result: new viral terms appear in ~10 minutes.

**Q3: How do you scale to 10K queries/second with < 50ms?**
> CDN caches the top 10K most-queried prefixes with 60-second TTL — handles ~80% of traffic. Cache misses hit stateless API servers that query Redis. Redis sorted-set ZREVRANGE is O(log N + K) — microseconds per query. With CDN absorbing 80% and Redis serving the rest, 10K QPS requires only 2-3 API server pods.

**Q4: How does personalization work?**
> On query, merge two suggestion lists: (1) Global top-K for the prefix (from trie). (2) User's recent searches matching the prefix (from Cassandra, partition key = user_id, cluster by recency). Weight recent user searches higher — show them first if matching. User history stored client-side for fastest access, synced to server for cross-device.

**Q5: How do you shard the trie for multi-language / multi-region?**
> Per-language shards: separate Redis clusters for English, Chinese, Spanish, etc. Within a language, shard by first 2 characters (676 buckets). Regions: CDN at the edge with regional PoPs; trie Redis clusters per region (replicated from central build). Prefix cache in CDN has 60s TTL — stale suggestions are acceptable.
