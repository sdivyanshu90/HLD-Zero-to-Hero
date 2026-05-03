# Uber Ride Sharing — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** geospatial, Redis GEOADD, location ingestion, matching, surge pricing  
**Companies:** Uber, Lyft, Ola, Grab

---

## Problem Statement

Design Uber's ride-sharing backend that:
- Handles 200K GPS updates/second from active drivers
- Matches riders to drivers within 5 seconds
- Shows real-time driver locations on a map
- Implements surge pricing based on supply-demand balance

---

## Architecture Diagram

```
Driver App (GPS every 4s)          Rider App
       │                               │
       ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│ Location Service │          │  Ride Request    │
│ (writes GPS)     │          │  Service         │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         ▼                             ▼
┌──────────────────────┐    ┌────────────────────────┐
│  Redis Geo Index     │    │  Driver Matching Svc   │
│  GEOADD driver:{id}  │───►│  GEORADIUS search      │
│  lat,lon             │    │  filter: available     │
└──────────────────────┘    └────────────────────────┘
         │                             │
         ▼                             ▼
┌──────────────────┐         ┌────────────────────┐
│  Kafka (events)  │         │  Trip DB           │
│  location_updates│         │  (PostgreSQL)      │
│  ride_events     │         └────────────────────┘
└──────────────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic and System Shape](02-traffic-and-system-shape.md)
3. [Location Ingestion](03-location-ingestion.md)
4. [Spatial Indexing](04-spatial-indexing.md)
5. [Driver Matching](05-driver-matching.md)
6. [Realtime Communication](06-realtime-communication.md)
7. [Kafka and Dynamic Pricing](07-kafka-and-dynamic-pricing.md)
8. [Checkpoint](08-checkpoint.md)
