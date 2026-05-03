# Step 1 — Requirements

## Functional Requirements

| # | Requirement | Notes |
|---|-------------|-------|
| F1 | Shorten a long URL to a compact short code | Output: `https://short.ly/aB3xK9z` |
| F2 | Redirect a short code to the original URL | HTTP 301 or 302 |
| F3 | Support optional TTL / expiration per URL | Default: never expire |
| F4 | Custom aliases (v2 scope) | E.g. `/my-brand-name` |
| F5 | Click analytics (v2 scope) | Count, geo, referrer |

## Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| N1 | High availability for redirects | 99.99 % uptime |
| N2 | Low redirect latency | p99 < 10 ms via cache |
| N3 | Short code uniqueness | Zero collisions globally |
| N4 | Durability of mappings | No data loss; replicated DB |
| N5 | Scalability | Handle 10× traffic spikes |

## Out of Scope (v1)

- Full analytics pipeline (Kafka + Flink)
- Abuse / spam detection
- User account system
- Custom domain management (e.g., `company.link/promo`)

## Clarifying Questions to Ask in Interview

1. "Should we support custom aliases in v1?"
2. "Is 301 (browser-caches redirect) or 302 (trackable) preferred?"
3. "What is the expected URL lifetime — do they expire?"
4. "Are there any rate limits per user/IP on creation?"
5. "Multi-region / global deployment needed?"

## Trade-Off Framing

```
Analytics scope
├─ No analytics  → simpler write path, smaller DB
├─ Async counter → low latency, eventual accuracy
└─ Sync counter  → accurate but adds write amplification

Redirect type
├─ 301 → browser caches, less server load, cannot track repeats
└─ 302 → every click hits server, full tracking, more load
```
