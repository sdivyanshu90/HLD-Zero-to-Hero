# Step 8 — Checkpoint & Interview Q&A

**Q1: Fan-out-on-write vs fan-out-on-read — when do you use each?**
> Fan-out-on-write (push model): tweet is written to all followers' feed caches immediately. Read is O(1) — just read the cache. Works for users with < 10K followers. Fan-out-on-read (pull model): fetch followed users' tweets at read time and merge. Works for celebrities (10M+ followers). Hybrid: push for normal users, pull for celebrities, merge on read.

**Q2: What data structure stores the feed in Redis?**
> Sorted Set (ZSET) with tweet_id as member and timestamp as score. ZREVRANGE retrieves latest tweets in O(log N + M). ZADD inserts new tweets in O(log N). ZREMRANGEBYRANK trims old tweets to bound memory per user.

**Q3: How do you handle a user who follows 10,000 accounts (power follower)?**
> On feed read, the k-way merge of 10,000 ZSET results becomes expensive. Optimization: cache the merged feed in Redis with a short TTL (1-2 minutes). Alternatively, limit the merge to a recent time window (e.g., last 7 days of tweets from followed accounts).

**Q4: How do you keep celebrity tweets appearing in followers' feeds near-real-time?**
> On read, the client fetches the fan-out feed (pre-computed) and the celebrity tweet lists (fetched lazily). A merge on read produces the final timeline. Latency is acceptable because fetching N celebrity tweet lists from Redis is fast (pipelined multi-get). Followed celebrity list is itself cached per user.

**Q5: How much memory does the Redis feed cache require at scale?**
> 800 entries/user × 16 bytes (score + ID) = 12.8 KB/user. For 50M active users: 50M × 12.8 KB = 640 GB. Needs a Redis cluster with ~8 nodes × 128 GB RAM. In practice, only active users (maybe 20% = 10M) have warm caches → ~128 GB total.
