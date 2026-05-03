# Content Delivery Networks (CDNs)

## What is a CDN?

A CDN is a globally distributed network of cache servers (Points of Presence, or PoPs) that serve content from the location nearest to the user.

```
Without CDN:
  User in Tokyo ──────────────────────────────▶ Origin (New York)
                              ~150ms RTT

With CDN:
  User in Tokyo ──▶ Tokyo PoP ──────────────────▶ Origin (New York)
                    ~5ms RTT       (only on cache miss, ~5% of requests)

  99% of requests: ~5ms (from Tokyo PoP cache)
  1% of requests:  ~155ms (cache miss, goes to origin)
  → 30× average latency improvement
```

---

## How CDN Caching Works

### Cache-Control Headers

The origin server tells the CDN how long to cache a response:

```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=86400      ← cache for 24 hours
Cache-Control: public, s-maxage=3600      ← CDN caches 1h, browser 0
Cache-Control: private                    ← don't cache in CDN (user-specific)
Cache-Control: no-cache                   ← must revalidate with origin on every request
Cache-Control: no-store                   ← never cache anywhere
ETag: "abc123"                             ← validator for conditional requests
```

### Cache Hit vs Miss Flow

```
First request (cache MISS):
  User ──▶ CDN PoP ──── origin pull ──▶ Origin Server
                    ◀─── response ────────────────────
           CDN caches response with TTL
  User ◀─── response ──

Second request (cache HIT, within TTL):
  User ──▶ CDN PoP
           (serves from cache immediately)
  User ◀─── response ── (no origin call)

After TTL expires (cache STALE):
  Option 1: Synchronous revalidation (stale-while-revalidate=0)
    User waits while CDN revalidates with origin
  Option 2: stale-while-revalidate=60
    User gets stale response immediately
    CDN revalidates in background
    Next user gets fresh response
```

### Cache Key

The CDN uses a cache key to determine if a response is cached. Default key: URL + Host:

```
Default cache key:
  https://cdn.example.com/api/products?category=shoes
  → Cached separately from:
  https://cdn.example.com/api/products?category=hats

Custom cache key variations:
  Include header: Vary: Accept-Language
  → English users and French users get separate cache entries

  Vary: Accept-Encoding
  → Gzipped and non-gzipped versions cached separately

  Vary: Cookie  ← DANGEROUS: creates one cache entry per cookie value
  → Effectively disables caching for authenticated users
```

---

## CDN Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     CDN GLOBAL ARCHITECTURE                       │
│                                                                    │
│    Origin Server (US-East)                                        │
│         │                                                          │
│         │ ← origin pull on cache miss only                        │
│         │                                                          │
│    ┌────▼─────────────────────────────────────────────┐          │
│    │              CDN BACKBONE                         │          │
│    │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │          │
│    │  │ Edge PoP │  │ Edge PoP │  │ Edge PoP │       │          │
│    │  │  US-East │  │  EU-West │  │  AP-East │       │          │
│    │  │  (NYC)   │  │  (LDN)   │  │  (TKY)   │       │          │
│    │  └────┬─────┘  └────┬─────┘  └────┬─────┘       │          │
│    └───────┼─────────────┼─────────────┼──────────────┘          │
│            │             │             │                           │
│         US users      EU users      APAC users                    │
│         ~5ms RTT      ~10ms RTT     ~8ms RTT                      │
└──────────────────────────────────────────────────────────────────┘
```

### Multi-Tier CDN (Shield / Mid-Tier Cache)

For popular CDNs, a second-tier "shield" PoP sits between edge PoPs and origin, absorbing origin traffic:

```
User ──▶ Edge PoP (miss) ──▶ Shield PoP (miss) ──▶ Origin
                             Shield PoP (hit after first miss)
                             → Origin gets N requests instead of N × number of edge PoPs

Example:
  500 edge PoPs worldwide, all miss at startup
  Without shield: 500 requests to origin for same content
  With shield: 1-10 requests to origin (one per shield region)
```

---

## CDN Use Cases

### Static Asset Delivery

```
Images, CSS, JS, fonts:
  Cache-Control: public, max-age=31536000, immutable
  (1 year cache for content-hashed assets)

  asset URL: /static/main.abc123.js
  → content hash in filename ensures cache busting on update

  CDN serves from edge indefinitely until filename changes
  → Origin receives zero requests for cached static assets
```

### API Response Caching

```
Product catalog (rarely changes):
  Cache-Control: s-maxage=300, stale-while-revalidate=60
  → CDN caches for 5 minutes, serves stale during revalidation

User-specific data (cannot be shared):
  Cache-Control: private, no-store
  → CDN does not cache; each user must go to origin

Vary: Accept header:
  Cache-Control: public, max-age=60
  Vary: Accept
  → JSON and XML responses cached separately per URL
```

### Dynamic Content Acceleration

Even non-cacheable requests benefit from CDN routing:

```
Without CDN:
  User (Tokyo) → Internet → Origin (New York)
  Route: variable, shared internet, 150ms RTT

With CDN routing:
  User (Tokyo) → CDN Tokyo PoP → CDN private backbone → Origin (New York)
  CDN uses dedicated fiber, optimal routing: ~80ms RTT

→ 50ms improvement even for non-cacheable dynamic requests!
```

---

## Cache Invalidation

Invalidation is one of the hardest problems in distributed systems. CDN invalidation options:

```
1. TTL-based expiry (natural):
   Content expires automatically after max-age
   → Zero operational overhead
   → Content may be stale for up to max-age after update

2. Purge (explicit invalidation):
   API call: DELETE /cache/key/https://example.com/product/123
   → Immediately removes from all CDN edge PoPs
   → Some CDNs propagate in seconds, others take minutes

3. Cache Buster (versioned URLs):
   /static/app.abc123.js → update to /static/app.def456.js
   → Old URL stays in cache (harmlessly), new URL is fresh
   → No purge needed, instant update

4. Surrogate-Key/Cache-Tag:
   Origin tags response: Surrogate-Key: product:123 category:shoes
   Invalidate all product:123 responses: single API call
   → Granular invalidation without knowing exact URLs
   Used by: Fastly, Cloudflare
```

---

## CDN Security Features

```
DDoS Mitigation:
  CDN absorbs attack traffic at the edge (L3/L4 scrubbing)
  Cloudflare: 280+ Tbps mitigation capacity (vs typical attacks of ~1 Tbps)

Web Application Firewall (WAF):
  Blocks OWASP Top 10 at CDN edge (SQLi, XSS, etc.)

Bot Management:
  Fingerprints and challenges bots (CAPTCHAs, JS challenges)
  Allows legitimate scrapers (Google, Bing)

TLS Offloading + Certificate Management:
  CDN terminates TLS at the edge
  Origin can use plain HTTP on private network (or mTLS for security)
  CDN manages certificate renewal automatically

Geographic Restriction:
  Block traffic from specific countries at CDN edge
```

---

## Interview Quick Answers

- **What is a CDN hit ratio and why does it matter?** — Percentage of requests served from CDN cache vs origin. 99% hit ratio → origin handles only 1% of traffic → origin can be 100× smaller.
- **Can you cache authenticated API responses in a CDN?** — Yes, but use `Vary: Authorization` or per-user cache keys, and be careful about privacy. Typically, per-user responses use `Cache-Control: private`.
- **How do you invalidate CDN cache across 200+ edge nodes?** — CDN providers offer purge APIs that propagate within seconds to minutes. For immediate updates, use versioned URLs (cache busting) — no purge needed.
- **Why is a CDN useful even for non-cacheable dynamic content?** — CDN provides TCP connection termination near the user and routes over private backbone to origin, reducing latency vs open internet routing.
