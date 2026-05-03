# Cheat Sheet: Distributed Web Crawler

## Scale (BoE)
```
Target: crawl 1B pages over 30 days
Pages per day: 1B / 30 ≈ 33M pages/day
Crawl QPS: 33M / 86,400 ≈ 400 pages/second
Average page size: 100 KB
Bandwidth: 400 × 100 KB = 40 MB/s = 320 Mbps (manageable)
Storage: 1B × 100 KB = 100 TB (compressed ~10-20 TB with dedup)
```

## System Diagram
```
Seed URLs ──▶ URL Frontier (Priority Queue)
                    │
              URL Scheduler (politeness delays per domain)
                    │
            ┌───────┼───────┐
            ▼       ▼       ▼
          Fetcher  Fetcher  Fetcher  (distributed workers)
            │
      Parse HTML (extract URLs + content)
            │
      ┌─────┴──────────────────┐
      ▼                        ▼
  Extracted URLs          Content Storage
  → Dedup check           (S3 / HDFS)
  → URL Frontier               │
                          Indexing Pipeline (Spark)
```

## URL Frontier Design

```
Priority queue with politeness:
  High priority: fresh, frequently updated pages (news sites)
  Low priority: rarely updated pages (old blog posts)
  
  Priority score:
    PageRank score × recency × update_frequency
  
  Politeness: don't hammer one domain too fast
    Maintain per-domain last_crawl_time
    Respect robots.txt crawl-delay directive
    Minimum 1 second between requests to same domain
    
  Per-domain queue:
    domain queue A: [url1, url2, url3] 
    domain queue B: [url4, url5]
    Scheduler: pick next URL ensuring domain politeness
```

## Deduplication

```
1. URL normalization:
   http://example.com/page  ==  https://example.com/page/  (after normalization)
   Normalize: lowercase, remove trailing slash, sort query params
   
2. URL dedup (Bloom filter):
   Bloom filter of all seen URLs (~10 bits per URL × 1B = 1.25 GB)
   Check before adding to frontier: if "definitely seen" → skip
   False positive rate 1%: OK (miss 1% of novel URLs)
   
3. Content dedup (SimHash or MD5):
   After downloading: compute hash of page content
   If hash seen before → near-duplicate → skip or merge
   SimHash: detects near-duplicate pages (90% similar content)
```

## Robots.txt Compliance

```
Fetch https://domain.com/robots.txt once per domain per crawl cycle
Cache robots.txt rules (Disallow: /private, Crawl-delay: 2)
Respect: skip disallowed URLs, honor crawl delays
Store robots.txt in Redis/DB per domain (TTL = 24h, then refresh)
```

## Unique Trick
The URL Frontier is the heart of the crawler. It must balance: freshness (crawl updated pages sooner), coverage (crawl broadly), and politeness (don't DDoS any one site). The two-level queue (priority across domains + per-domain queue with politeness delay) solves all three simultaneously.
