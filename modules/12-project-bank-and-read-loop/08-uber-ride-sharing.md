# Cheat Sheet: Uber Ride Sharing

## Scale (BoE)
```
Concurrent drivers: 1M (globally)
Concurrent riders: 5M
Location updates: drivers send GPS every 5 seconds
Location update QPS: 1M / 5 = 200K location writes/second
Ride matching: 500K new rides/hour = ~140 ride requests/second
```

## System Diagram
```
Driver App ──GPS every 5s──▶ Location Service ──▶ Redis Geospatial Index
                                                   (GEOADD)

Rider requests ride ──▶ Matching Service
                              │
                    1. Lookup nearby drivers in geospatial index
                       GEORADIUSBYMEMBER driver:locations {rider_lat} {rider_lon} 5 km
                    2. Get top 5 candidates by proximity + availability
                    3. Offer ride to nearest driver (with timeout)
                    4. If declined/timeout → offer to next driver
                              │
                         Accept ──▶ Create Trip record in DB
                                    Assign driver to rider
                                    Start real-time tracking (WebSocket)
```

## Key Design Decisions

**1. Geospatial indexing:**
- Redis GEOAPP: stores (lat, lon) as geohash in sorted set
  - GEOADD key lon lat member
  - GEORADIUS key lon lat radius km → returns members within radius
  - O(N+log M) for radius query, perfectly suited
- Alternative: PostGIS (PostgreSQL extension) for persistent geospatial data

**2. Location update frequency:**
- 200K writes/second for GPS updates → Redis handles easily (single-threaded, 1M ops/s)
- Only store CURRENT location (drivers) in Redis (update in place, not historical)
- Historical trip path: stored in DB after trip ends

**3. Surge pricing:**
- Heatmap: count available drivers vs active ride requests per geohash cell
- If rides / drivers > threshold → surge multiplier applies
- Precomputed per geohash bucket, refreshed every 30s

## Bottlenecks
1. Matching hotspot: airport/station → thousands of drivers + riders in 1 geohash cell
   → Partition matching work, not a single matching service
2. ETA calculation: requires routing graph → Google Maps API or self-hosted OSRM

## Unique Trick
Redis Geospatial commands (GEOADD, GEORADIUS) are built on sorted sets with geohash encoding. A single Redis command can find all drivers within 5 km in O(log N). Store driver availability as a separate SET, and do intersection of geospatial result with availability set.
