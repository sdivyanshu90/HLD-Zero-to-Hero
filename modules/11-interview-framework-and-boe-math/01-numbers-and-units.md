# Numbers and Units Every Engineer Must Know

## Powers of 2 Table

```
Power    Value              Approximation    Common Usage
────────────────────────────────────────────────────────────────
2^10     1,024              ~1K              kilobyte (1 KB = 1024 bytes)
2^20     1,048,576          ~1M              megabyte (1 MB)
2^30     1,073,741,824      ~1B              gigabyte (1 GB)
2^32     4,294,967,296      ~4B              IPv4 address space, max 32-bit int
2^40     ~1.1 trillion      ~1T              terabyte (1 TB)
2^50     ~1.1 quadrillion   ~1P              petabyte (1 PB)
2^64     ~18.4 quintillion  ~18 EB           UUID space, 64-bit int
```

---

## Storage Units

```
1 KB  = 1,024 bytes    ≈ 1,000 bytes
1 MB  = 1,024 KB       ≈ 1 million bytes
1 GB  = 1,024 MB       ≈ 1 billion bytes
1 TB  = 1,024 GB       ≈ 1 trillion bytes
1 PB  = 1,024 TB       ≈ 1 quadrillion bytes
1 EB  = 1,024 PB       ≈ 1 quintillion bytes

Rule of thumb for BoE:
  Treat 1 KB ≈ 10^3, 1 MB ≈ 10^6, 1 GB ≈ 10^9 (decimal approximation)
  Error is only ~2.4%, negligible for estimation

Real-world sizes:
  1 ASCII character:   1 byte
  UUID:                36 bytes (string) or 16 bytes (binary)
  Tweet (text):        ~140-280 bytes
  Email:               ~50-100 KB
  Phone number:        ~15 bytes
  Typical JSON row:    ~500 bytes - 1 KB
  Web page HTML:       ~50-100 KB
  HD photo (JPEG):     ~3-5 MB
  4K video frame:      ~8 MB (uncompressed) → ~1 MB (H.265)
  1 minute of video:   ~200 MB (1080p, H.264)
  1 hour of video:     ~1-4 GB (depends on quality)
  
Common record sizes (for BoE storage estimation):
  User account row:         ~1 KB
  URL mapping:              ~500 bytes
  Tweet/post:               ~200-500 bytes  
  Chat message:             ~200 bytes
  Database index entry:     ~50-100 bytes
  Redis key-value entry:    ~100-300 bytes
```

---

## Time Units

```
1 nanosecond (ns)  = 10^-9 second  = 0.000000001s
1 microsecond (µs) = 10^-6 second  = 1,000 ns
1 millisecond (ms) = 10^-3 second  = 1,000 µs  = 1,000,000 ns
1 second (s)
1 minute           = 60s
1 hour             = 3,600s
1 day              = 86,400s         ≈ 10^5 seconds (very useful!)
1 week             = 604,800s        ≈ 6×10^5 s
1 month            = 2,592,000s      ≈ 2.5×10^6 s
1 year             = 31,536,000s     ≈ 3×10^7 s (30 million seconds)

Memorable approximations:
  1 day ≈ 100K seconds (86,400 ≈ 10^5)
  1 month ≈ 2.5M seconds
  1 year ≈ 30M seconds

These are critical for QPS calculations:
  1M DAU, each does 1 request/day:
  QPS = 1,000,000 / 86,400 ≈ 12 QPS (very low!)
  
  1M DAU, each does 100 requests/day:
  QPS = 100,000,000 / 86,400 ≈ 1,160 QPS ≈ 1.2K QPS
```

---

## Request Rate Reference

```
QPS (Queries Per Second) scale:
  1 QPS    → trivial (local dev)
  100 QPS  → small app (single server easily handles)
  1K QPS   → medium app (need to start thinking about architecture)
  10K QPS  → large app (need horizontal scaling, caching)
  100K QPS → very large app (Uber, Twitter-scale writes)
  1M QPS   → extreme scale (Google search, AWS)

Conversion: RPS (requests/sec), QPS, TPS (transactions/sec) are often used interchangeably

DAU to QPS formula:
  QPS = (DAU × requests_per_day_per_user) / 86,400
  
  Peak QPS:
  Peak = Average QPS × peak_multiplier
  Typical peak_multiplier: 2× to 10×
  → 2× for steady traffic (business apps)
  → 5-10× for consumer apps with peak hours (lunch, evening)

Twitter example:
  300M DAU, each views ~100 tweets/day = 30 tweets + 70 other actions
  Average QPS = (300M × 100) / 86,400 = 347K QPS average read
  Peak QPS = 347K × 3 ≈ 1M QPS at peak
```

---

## Bandwidth Units

```
1 Kbps  = 1,000 bits/second   (kilobits per second)
1 Mbps  = 1,000,000 bits/sec  = 125 KB/s
1 Gbps  = 10^9 bits/sec       = 125 MB/s
1 Tbps  = 10^12 bits/sec      = 125 GB/s

Common bandwidths:
  4G mobile:          20-100 Mbps download
  Home broadband:     100 Mbps - 1 Gbps
  Data center NIC:    1 Gbps, 10 Gbps, 25 Gbps
  CDN edge server:    10 Gbps
  Internet backbone:  100 Gbps - Tbps

Bandwidth calculation:
  Request size × QPS = bandwidth required
  
  Example:
    10K QPS, average response = 10 KB
    10,000 × 10,000 bytes = 100,000,000 bytes/s = 100 MB/s = 800 Mbps
    → Need ~1 Gbps network capacity (with headroom)
```

---

## Interview Quick Answers

- **How many seconds in a day?** — 86,400 ≈ 10^5. This is the key number for QPS calculations. Every interview estimation that involves "per day" divides by 86,400 (or approximated as 100K for BoE math).
- **What is 1 petabyte in perspective?** — 1 PB = 1,000 TB = 1,000,000 GB. Facebook stores hundreds of PBs of data. A typical large database is ~10-100 TB. 1 PB ≈ 1 million 1-GB files or ~200 years of HD video.
