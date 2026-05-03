# Module 12: Project Bank and Read Loop

## Overview

This module is your interview preparation war room — one cheat sheet per system, containing the condensed design decisions, bottlenecks, scale numbers, and key trade-offs for 20 major system design problems.

---

## How to Use This Module

```
Strategy: Spaced Repetition + Active Recall

Week 1: Read cheat sheets for easy systems (01-06)
Week 2: Read cheat sheets for medium systems (07-12)
Week 3: Read cheat sheets for hard systems (13-21)
Week 4: Review all, practice drawing diagrams from memory

Daily Read Loop (30 min):
  Day 1: Re-read 3 cheat sheets from memory (draw, then verify)
  Day 2: Whiteboard one full design without notes
  Day 3: Do the BoE math for 3 systems
  Day 4: Identify bottlenecks and optimizations for 3 systems
  Repeat cycle
```

---

## Project Index

| # | System | Difficulty | Key Pattern |
|---|--------|------------|-------------|
| 02 | [URL Shortener](02-url-shortener.md) | Easy | Cache-aside, hashing |
| 03 | [Distributed ID Generator](03-distributed-id-generator.md) | Easy | Snowflake, bit layout |
| 04 | [Distributed Cache](04-distributed-cache.md) | Easy | Consistent hashing, eviction |
| 05 | [Distributed Rate Limiter](05-distributed-rate-limiter.md) | Medium | Token bucket, Redis atomic |
| 06 | [Ticket Booking System](06-ticket-booking-system.md) | Medium | Optimistic locking, two-phase reserve |
| 07 | [Twitter Newsfeed](07-twitter-newsfeed.md) | Medium | Fan-out, pub-sub, graph traversal |
| 08 | [Uber Ride Sharing](08-uber-ride-sharing.md) | Medium | Geospatial indexing, real-time matching |
| 09 | [Collaborative Text Editor](09-collaborative-text-editor.md) | Hard | OT/CRDT, WebSocket |
| 10 | [Video Streaming](10-video-streaming-platform.md) | Hard | CDN, adaptive bitrate |
| 11 | [Realtime Chat](11-realtime-chat-system.md) | Medium | WebSocket, message ordering |
| 12 | [Notification System](12-notification-system.md) | Medium | Fan-out, priority queues |
| 13 | [Distributed File Storage](13-distributed-file-storage.md) | Hard | Chunking, consistent hashing |
| 14 | [Search Autocomplete](14-search-autocomplete.md) | Medium | Trie, prefix caching |
| 15 | [Web Crawler](15-distributed-web-crawler.md) | Hard | BFS, dedup, politeness |
| 16 | [Payment Ledger](16-payment-ledger-platform.md) | Hard | Double-entry, idempotency |
| 17 | [Food Delivery](17-food-delivery-platform.md) | Hard | Real-time location, ETA |
| 18 | [Ad Click Aggregation](18-ad-click-aggregation.md) | Hard | Stream processing, windowing |
| 19 | [Service Discovery](19-service-discovery-and-config.md) | Hard | Raft consensus, health checks |
| 20 | [Metrics Monitoring](20-metrics-monitoring-and-alerting.md) | Hard | Time-series DB, alerting |
| 21 | [Multiplayer Game Backend](21-realtime-multiplayer-game-backend.md) | Hard | UDP, game state sync |
