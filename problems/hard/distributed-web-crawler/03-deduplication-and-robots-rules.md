# Step 3 — Deduplication and Robots Rules

## URL Deduplication with Bloom Filter

```
Problem: 1 B URLs; must check "have we seen this URL before?"

Naive: Hash set in memory
  1 B URLs × 50 bytes = 50 GB → too large for one machine

Solution: Bloom Filter
  n = 1 B, p = 0.001 (0.1% false positive rate)
  m = -n × ln(p) / (ln 2)^2 = 1.44 B bytes = 1.44 GB
  k = (m/n) × ln 2 = 10 hash functions

FP rate 0.1%: we skip 1 in 1000 URLs we haven't seen
  → acceptable (we'll re-encounter them in the next crawl)

Implementation: Redis BitField or Java Bloom filter (Guava)
  Partitioned across 4 Redis nodes (360 MB each)
```

## URL Normalization

```
Before inserting into bloom filter, normalize:
  1. Lowercase scheme and host:   HTTP://Example.COM → http://example.com
  2. Remove default port:         http://example.com:80/ → http://example.com/
  3. Sort query params:           ?b=2&a=1 → ?a=1&b=2
  4. Remove fragment:             #section → removed
  5. Resolve relative URLs:       /path → http://example.com/path
  6. Remove tracking params:      ?utm_source=... → removed

After normalization, URLs that look different may be identical:
  http://Example.com/Page → http://example.com/page
```

## robots.txt Compliance

```
robots.txt rules:
  User-agent: *
  Disallow: /private/
  Disallow: /admin/
  Crawl-delay: 10

Fetching robots.txt:
  1. On first visit to domain, fetch http://{domain}/robots.txt
  2. Cache in Redis: robots:{domain} → parsed rules, TTL 24h
  3. Check every URL against cached rules before fetching
  4. Respect Crawl-delay (time between requests to same domain)

Edge cases:
  robots.txt returns 404 → no restrictions (crawl everything)
  robots.txt returns 500 → treat as "disallow all" (retry later)
  robots.txt > 500 KB → parse only first 500 KB (Google policy)
```

## Content Deduplication (SimHash)

```
Problem: Different URLs may have near-identical content
  (duplicate pages, slight variations)

SimHash approach:
  1. Extract text from HTML
  2. Compute weighted feature hash (shingles)
  3. 64-bit simhash value
  4. Two pages are near-duplicate if hamming_distance(h1, h2) ≤ 3

Storage: Simhash index (sorted table of hash values)
  Lookup: find all stored hashes within Hamming distance 3
  Efficient implementation: divide 64 bits into 4 blocks of 16,
    store in 4 tables, match on any block (birthday paradox)

Store simhash in crawl DB:
  Skip content processing for near-duplicates
```
