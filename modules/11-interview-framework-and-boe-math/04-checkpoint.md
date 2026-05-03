# Module 11 Checkpoint: Interview Framework and BoE Math

## Questions

---

**Q1.** Perform a BoE estimation for a notification system. Assumptions: 500M users, each receives ~20 notifications/day (push, email, SMS).

> **Answer:**
> - Notification rate: 500M × 20 / 86,400 ≈ 115K notifications/second average
> - Peak: 115K × 3 = 345K/s peak (or ~350K QPS)
> - Notification size: ~200 bytes (device_token, user_id, message, payload)
> - Daily storage (if we store): 500M × 20 × 200 bytes = 2 TB/day
> - With 30-day retention: 60 TB
> - With replication: 180 TB
> - Channels: push (~60%, 200M), email (~30%, 150M), SMS (~10%, 50M) per day
> - Push: 200M/day / 86400 = 2,300/s → need 3 push notification service workers
> - SMS: 50M/day at ~$0.01/SMS = $500K/day → optimization priority!

---

**Q2.** A user uploads a 4K video (2 GB) to a video platform. Estimate the storage, processing, and CDN requirements for this.

> **Answer:**
> - Raw storage: 2 GB (single copy), with replication: 6 GB
> - Transcoding: convert to multiple resolutions (4K, 1080p, 720p, 480p)
>   - 1080p is ~25% the size of 4K: ~500 MB; 720p: ~200 MB; 480p: ~100 MB
>   - Total per video: 2000 + 500 + 200 + 100 = ~2.8 GB per video × replication = ~8 GB
> - Processing time: transcoding at 1× realtime → 2 GB video → ~30 minutes of 4K
>   Actually: GPU-accelerated → 10× faster → 3 minutes
> - CDN: if 1M users watch this video × 1 GB average (720p):
>   1M × 1 GB = 1 PB of CDN bandwidth

---

**Q3.** Estimate the BoE for Twitter's tweet storage. 300M DAU, 5 tweets/day/user.

> **Answer:**
> - Tweets per day: 300M × 5 = 1.5B tweets/day
> - Write QPS: 1.5B / 86,400 ≈ 17,400 writes/second
> - Tweet size: text 280 chars (~280 bytes) + metadata (user_id, timestamp, likes, retweets, etc.) ≈ 500 bytes
> - Daily storage: 1.5B × 500 bytes = 750 GB/day
> - With 3× replication: 2.25 TB/day
> - Per year: 2.25 TB × 365 ≈ 820 TB/year ≈ ~1 PB/year (consistent with Twitter's known scale)
> - This does NOT include media (images, videos) which would be 10-100× more

---

**Q4.** Given 12K read QPS and a Redis cache with 95% hit rate, how many DB reads per second hit the database?

> **Answer:** Cache hit rate = 95% → cache miss rate = 5%
> DB reads/second = 12K × 5% = 600 reads/second
> Each DB server handles ~5K QPS (with indexing, no joins): 600/5000 < 1 server → a single DB read replica can handle this comfortably.
> Key insight: cache hit rate of 95% reduces DB load from 12K to 600 (20× reduction). Going from 95% to 99% hit rate further reduces to 120 reads/second (5× more reduction from 4% improvement).

---

**Q5.** You're designing a rate limiter. What algorithm would you choose for an API that should allow 100 requests/minute with burst of 20 requests/second?

> **Answer:** Use a **Token Bucket**:
> - Bucket capacity: 20 tokens (allows burst of 20)
> - Refill rate: 100/60 ≈ 1.67 tokens/second
> - Implementation: Redis key per user, INCR+TTL for fixed window counter (simpler) or sorted set for sliding window log
> - The sliding window counter (two fixed windows, weighted) gives accurate enforcement without race conditions
> 
> Why not sliding window log? Memory: user with high traffic stores many timestamps
> Why not fixed window? Allows 200 requests in 1-second boundary window
> Token bucket: best balance of burst allowance + sustained rate enforcement with O(1) Redis operations

---

## Checklist

- [ ] Storage units: KB/MB/GB/TB and when to use each
- [ ] 86,400 seconds/day (the key conversion number for QPS estimation)
- [ ] BoE formula: DAU × requests/day / 86,400 = average QPS
- [ ] Peak QPS = average × peak_multiplier (2-10×)
- [ ] Storage formula: writes/day × record_size × 365 × replication
- [ ] RADIO framework: Requirements, API, Data, Infrastructure, Optimizations
- [ ] Always clarify read:write ratio (changes design completely)
- [ ] Common record sizes: tweet ~300B, user ~1KB, photo metadata ~500B
- [ ] Cache hit rate effect: 95% hit → 5% miss → 20× DB load reduction
