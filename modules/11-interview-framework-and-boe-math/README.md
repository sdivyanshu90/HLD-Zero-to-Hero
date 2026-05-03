# Module 11: Interview Framework and BoE Math

## Overview

This module gives you the quantitative tools and structured approach to ace any system design interview. The BoE (Back-of-the-Envelope) math is what separates engineers who "just draw boxes" from those who make justified design decisions.

---

## What You Will Learn

```
┌────────────────────────────────────────────────────────────────┐
│              MODULE 11 LEARNING MAP                             │
│                                                                  │
│  01-numbers-and-units                                           │
│     └── Storage (KB/MB/GB/TB), time (1 day ≈ 86,400s)         │
│         QPS reference numbers, bandwidth                        │
│                    │                                            │
│                    ▼                                            │
│  02-qps-and-capacity-estimation                                 │
│     └── DAU → QPS formula, storage formula, bandwidth          │
│         Compute estimation, scale reference table              │
│                    │                                            │
│                    ▼                                            │
│  03-system-design-interview-framework                          │
│     └── RADIO (Requirements, API, Data, Infra, Optimizations)  │
│         Per-step guidance, common mistakes, timing             │
└────────────────────────────────────────────────────────────────┘
```

---

## The Most Important Numbers

```
Memorize these for any interview:

Number          Value        Use
───────────────────────────────────────────────────────
1 day           86,400 s     QPS conversion
1 year          31,536,000 s (~30M s) storage estimation
1 KB            ~1,000 bytes  record sizing
1 MB            ~10^6 bytes   
1 GB            ~10^9 bytes
1 TB            ~10^12 bytes
Tweet size      ~300 bytes    storage BoE
User record     ~1 KB         storage BoE
P99 latency:
  L1 cache hit  ~1 ns
  RAM           ~80 ns
  Redis         ~0.5 ms
  DB query      ~1-10 ms
  Cross-region  ~100 ms
```

---

## Files in This Module

| File | Topic |
|------|-------|
| [01-numbers-and-units.md](01-numbers-and-units.md) | Storage, time, bandwidth reference |
| [02-qps-and-capacity-estimation.md](02-qps-and-capacity-estimation.md) | BoE calculation formulas with examples |
| [03-system-design-interview-framework.md](03-system-design-interview-framework.md) | RADIO framework, step-by-step guide |
| [04-checkpoint.md](04-checkpoint.md) | Practice estimation problems |
