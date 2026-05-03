# Distributed Web Crawler — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** URL frontier, bloom filter, politeness, robots.txt, dedup  
**Companies:** Google, Bing, Common Crawl, Ahrefs

---

## Problem Statement

Design a distributed web crawler that:
- Crawls 1 B URLs in 30 days (consistent crawl of the whole web)
- Respects robots.txt and per-domain rate limits (politeness)
- Deduplicates URLs and near-duplicate content
- Stores raw HTML and extracted links for downstream processing

---

## Architecture Diagram

```
Seed URLs
    │
    ▼
┌───────────────────────────────────────────┐
│  URL Frontier                              │
│  Priority Queue (Kafka-backed)             │
│  + Per-domain politeness queue             │
└──────────────┬────────────────────────────┘
               │
       ┌───────┴──────┐
       ▼              ▼
┌────────────┐  ┌────────────┐
│ Fetcher 1  │  │ Fetcher N  │  HTTP/HTTPS workers
└─────┬──────┘  └─────┬──────┘
      │               │
      ▼               ▼
┌─────────────────────────────┐
│  HTML Parser Service        │
│  Extract: links, metadata   │
└──────────┬──────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
 New URLs     Parsed Content
 (back to     (to S3 + Index)
  frontier)
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [URL Frontier and Scheduling](02-url-frontier-and-scheduling.md)
3. [Deduplication and Robots Rules](03-deduplication-and-robots-rules.md)
4. [Fetcher Architecture](04-fetcher-architecture.md)
5. [Parser and Storage Pipeline](05-parser-and-storage-pipeline.md)
6. [Politeness and Rate Control](06-politeness-and-rate-control.md)
7. [Failure Recovery and Observability](07-failure-recovery-and-observability.md)
8. [Checkpoint](08-checkpoint.md)
