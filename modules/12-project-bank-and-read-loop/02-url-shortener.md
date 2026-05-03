# Cheat Sheet: URL Shortener

## Scale (BoE)
```
DAU: 100M
Writes (create URL): 1M/day → ~12 WPS
Reads (redirect):    100M/day → ~1,150 RPS (average), 6K RPS (peak)
Read:Write ratio:    ~100:1

Storage per URL:  ~130 bytes (code + long_url + metadata)
Daily writes:     1M × 130 bytes = 130 MB/day → ~50 GB/year (small!)
```

## Core Data Model
```
urls:
  short_code   VARCHAR(7) PK
  long_url     TEXT
  user_id      BIGINT
  created_at   TIMESTAMP
  expires_at   TIMESTAMP

Index: (user_id) for user's URL management
Sharding: not needed at this scale (50 GB total after 10 years)
```

## System Diagram
```
Client ──GET /{code}──▶ CDN (cache 301/302) ──miss──▶ Redirect Service
                                                            │
                                                       Redis cache
                                                       code→long_url
                                                            │ miss
                                                       PostgreSQL
                                                       (read replica)

Write path:
Client ──POST /urls──▶ API Gateway ──▶ URL Service ──▶ PostgreSQL (primary)
                                           │
                                      ID Generator (short code)
```

## Key Design Decisions

**1. Short Code Generation:**
- Option A: Base62 encode auto-increment ID (1→"1", 62→"10", 3.5B→7 chars)
  - Sequential IDs are predictable → security risk (enumerate all URLs)
  - Simple, no collision
- Option B: Random 7-char Base62 = 62^7 = 3.5 trillion combinations
  - Check DB for collision, retry if exists
  - Non-guessable
- **Choice: Option B (random)** for non-guessability; use bloom filter to check collision O(1)

**2. 301 vs 302 Redirect:**
- 301 Permanent: browser caches → cannot change destination, analytics miss return visits
- 302 Temporary: no browser cache → every redirect hits your server → analytics work
- **Choice: 302** if analytics needed; **301** if you want to offload traffic to browser cache

## Bottlenecks
1. Read path: solved by Redis cache (99%+ hit rate expected)
2. Write path: very low (12 WPS), no special scaling needed

## Unique Trick
URL redirect is a pure cache problem. The entire "database" after 10 years is ~50 GB — fits on a single machine. The challenge is latency (must be < 50ms), not storage or throughput.
