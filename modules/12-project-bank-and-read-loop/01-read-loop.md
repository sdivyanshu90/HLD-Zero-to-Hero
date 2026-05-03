# The Read Loop: How to Use This Module

## The Problem with System Design Prep

Most engineers read a solution once, feel like they understand it, and move on. In an interview, they can't reconstruct it from scratch. The fix: **active recall with spaced repetition**.

---

## The Active Recall Method

```
Step 1: Read the cheat sheet carefully (first time)
Step 2: Close the cheat sheet
Step 3: Draw the architecture from memory on a whiteboard or paper
  - Core components
  - Data flow arrows
  - Key scaling choices
Step 4: Open the cheat sheet, compare, identify gaps
Step 5: Re-read the gaps
Step 6: Repeat step 2-5 after 1 day, then 3 days, then 7 days

Each repetition takes 5-10 minutes.
After 3 repetitions, you can reconstruct 90% from memory.
```

---

## Read Loop Schedule

```
Day 1:  URL Shortener, ID Generator, Distributed Cache (new reads)
Day 2:  Draw URL Shortener from memory; Rate Limiter, Ticket Booking (new reads)
Day 3:  Draw ID Generator, Rate Limiter from memory; Twitter, Uber (new reads)
Day 4:  Draw Distributed Cache, Ticket Booking from memory; Chat, Notification (new)
Day 5:  Draw Twitter, Uber from memory; File Storage, Autocomplete (new)
...

The pattern:
  Each day: draw yesterday's reads + read 2-3 new cheat sheets
```

---

## What to Focus On Per Cheat Sheet

```
For each system, know:
  1. BoE: scale numbers (DAU, QPS, storage)
  2. Core data model: 2-3 key tables/collections
  3. System diagram: 5-8 components, their connections
  4. Hot path: the most critical performance path (latency-sensitive)
  5. Two key bottlenecks: what will break first under load?
  6. Two key trade-offs: the design decisions with alternatives
  7. One unique trick: the insight that makes this system work
```

---

## Interview Signals Cheat Sheet

```
Signal: Shows scale awareness
  Evidence: "At 100M DAU with 10 reads/day, that's ~12K QPS read..."
  Evidence: "This means Redis will see 99% hit rate, ~100 DB misses/sec..."

Signal: Understands bottlenecks
  Evidence: "The bottleneck here is the fan-out on write for celebrities..."
  Evidence: "DB writes will bottleneck first — we should shard on user_id..."

Signal: Proposes trade-offs (not "best" solutions)
  Evidence: "I could use strong consistency here, but that adds 2ms latency..."
  Evidence: "Fan-out on write is simpler but won't scale for users with 10M followers..."

Signal: Considers failure modes
  Evidence: "If Redis is down, reads fall through to DB — we need circuit breaker..."
  Evidence: "If the payment charge succeeds but we crash before recording: use idempotency key..."
```
