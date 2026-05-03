# QPS and Capacity Estimation

## The Four-Step BoE Framework

Back-of-the-Envelope (BoE) estimation:

```
1. Define the system's scale: DAU, QPS, data per request
2. Estimate storage needs: data size × retention period
3. Estimate bandwidth: QPS × request/response size
4. Estimate compute: QPS ÷ requests_per_server
```

---

## Step 1: Scale (DAU → QPS)

```
Formula:
  QPS = (DAU × avg_requests_per_day) / 86,400

  DAU examples:
    Small startup:    100K DAU
    Medium product:   1M DAU
    Large product:    10-50M DAU (Twitter, Snapchat)
    Very large:       100M+ DAU (Facebook, YouTube)

  Requests per day per user (examples):
    URL shortener:    5-10 redirects/day (mostly reads)
    Twitter:          30-50 timeline refreshes + 5-10 posts
    Instagram:        50-100 feed loads + 3-5 posts/stories
    Uber:             2-5 ride requests (very low frequency)
    Netflix:          1-3 movie sessions
    Slack/Chat:       200-500 messages/day (high frequency)

BoE QPS worked example: URL Shortener
  Assumption: 100M DAU
  - Reads (redirects): 10 per user per day
  - Writes (new short URLs): 0.1 per user per day (10M URLs/day)
  
  Read QPS  = (100M × 10) / 86,400 ≈ 11,600 QPS ≈ 12K QPS
  Write QPS = (100M × 0.1) / 86,400 ≈ 115 QPS
  
  Peak read QPS: 12K × 5 (peak factor) ≈ 60K QPS peak
  
  Read:Write ratio ≈ 100:1
```

---

## Step 2: Storage Estimation

```
Formula:
  Storage per year = QPS_write × record_size × seconds_per_year × replication_factor

  Or equivalently:
  Storage per year = writes_per_day × record_size × 365 × replication_factor

URL Shortener continued:
  Writes per day: 100M × 0.1 = 10M URLs/day
  Record size:
    short_code: 7 bytes
    long_url:   ~100 bytes
    created_at: 8 bytes
    user_id:    8 bytes
    Total:      ~130 bytes per URL
  
  Daily storage: 10M × 130 bytes = 1.3 GB/day
  Annual:        1.3 GB × 365    = ~475 GB/year ≈ ~0.5 TB/year
  
  With replication factor 3:
    0.5 TB × 3 = 1.5 TB/year of raw disk
  
  10-year storage: 1.5 TB/year × 10 = 15 TB total (very manageable!)

Common record size estimations:
  Tweet:           ~300 bytes (text + metadata)
  User profile:    ~1 KB
  Photo metadata:  ~500 bytes (actual image stored separately)
  Chat message:    ~200 bytes
  Ride booking:    ~500 bytes
  Video metadata:  ~1 KB (actual video stored separately/CDN)
```

---

## Step 3: Bandwidth Estimation

```
Formula:
  Bandwidth = QPS × avg_response_size_bytes × 8 / 1,000,000 (Mbps)
  or simply: QPS × avg_response_size → bytes/sec

URL shortener (read path):
  Read QPS: 12K
  Response: HTTP 301 redirect (~200 bytes header)
  Bandwidth: 12,000 × 200 bytes = 2.4 MB/s = ~19 Mbps
  → Trivial! URL redirect is not bandwidth-constrained

Instagram feed (image-heavy):
  Feed QPS: 50M DAU × 50/day / 86,400 ≈ 29K QPS
  Each feed: 20 photo thumbnails, each 50 KB
  Response size: 20 × 50 KB = 1 MB per feed request
  Bandwidth: 29K × 1 MB = 29 GB/s = 232 Gbps!
  → CDN is essential (can't serve this from origin)
  CDN: distribute across thousands of PoPs globally

Video streaming (per user):
  1 user watching 1080p: ~5 Mbps
  1M concurrent users: 5 Mbps × 1M = 5 Tbps
  → Netflix has CDN servers in every major ISP for this reason
```

---

## Step 4: Compute Estimation

```
How many servers do we need?

Formula:
  servers = QPS / (requests_per_server_per_second × availability_headroom)

Requests per server (rough estimate):
  Simple API (no DB, in-memory): 10,000-50,000 QPS
  API with DB reads (cached): 5,000-20,000 QPS
  API with DB writes: 1,000-5,000 QPS
  CPU-heavy processing: 100-1,000 QPS

URL shortener:
  60K peak QPS (read)
  Each server handles 10K QPS (Redis + minimal logic)
  Servers needed = 60K / 10K = 6 servers
  With 50% headroom: 12 servers
  Plus: load balancers (2 for HA), Redis cluster (6 nodes), DB (primary + replica)

Reality check:
  Most BoE doesn't need exact server count
  Show: "~10s of servers for app tier, Redis cluster for caching"
  Key: identify if the design is I/O bound, CPU bound, or bandwidth bound
```

---

## Quick Reference: Capacity by Scale

```
Scale         DAU      Read QPS     Write QPS    Storage/year
──────────────────────────────────────────────────────────────────
Startup       100K     100-500      10-50        10-50 GB
Small         1M       500-5K       50-500       50-500 GB
Medium        10M      5K-50K       500-5K       500 GB-5 TB
Large         100M     50K-500K     5K-50K       5 TB-50 TB
Very Large    1B+      500K-5M      50K-500K     50+ TB
```

---

## Interview Quick Answers

- **Walk me through a BoE for Twitter.** — DAU=300M, each posts 5 tweets/day + views 50 tweets. Write QPS = 300M×5/86400 ≈ 17K. Read QPS = 300M×50/86400 ≈ 173K. Tweet size ≈ 300 bytes. Daily write storage = 17K×300×86400 ≈ 440 GB/day. With 3× replication = 1.3 TB/day raw. Per year ≈ 475 TB. This aligns with known Twitter data volumes.
- **How do you estimate peak QPS?** — Multiply average QPS by a peak factor (2-10×). Consumer apps peak in evenings/weekends. For US app: 5-8 PM Eastern is peak. Peak = average × 3-5 is a common assumption. Always build for 2-3× expected peak to handle viral events.
