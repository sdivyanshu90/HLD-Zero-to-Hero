# Step 4 — Spatial Indexing

## The Problem

```
Find all available drivers within 5 km of rider (lat=37.7749, lon=-122.4194)

Naive: scan all 500K active drivers, compute distance for each → O(N)
Goal: sub-second query for nearby drivers → need spatial index
```

## Redis GEO Commands

```
# Store driver location
GEOADD drivers:{city} -122.4194 37.7749 "driver_123"
GEOADD drivers:{city} -122.4100 37.7800 "driver_456"

# Find drivers within 5 km
GEORADIUS drivers:{city} -122.4194 37.7749 5 km ASC COUNT 10
→ ["driver_456", "driver_123"]  (sorted by distance)

# Get distance to specific driver
GEODIST drivers:{city} driver_123 driver_456 km
→ "0.9231"

# Implementation: uses Geohash internally
# Geohash precision: Redis uses 52-bit encoding ≈ 0.6mm accuracy
```

## Geohash Grid

```
Geohash divides Earth into a grid of cells:
  Precision 6: ~1.2 km × 0.6 km cells (6 chars: "9q8yyk")
  Precision 7: ~153 m × 153 m cells  (7 chars: "9q8yykz")

Neighbour search: a driver at geohash "9q8yyk" + 8 neighbours
  covers a 3×3 grid ≈ 11 km² area → get all drivers in that area

Advantages of Geohash over naive distance:
  - Index: just string prefix match
  - DB index on geohash prefix is a B-tree index (existing DB feature)
  - Partition data: each geohash cell = a separate shard
```

## S2 Cells (Google Maps / Uber S2)

```
S2 library divides sphere into cells at 30 levels:
  Level 12: ~3.3 km edge length
  Level 14: ~830 m edge length
  Level 16: ~207 m edge length
  Level 18: ~52 m edge length

Advantages over Geohash:
  - Cells are more uniformly sized (Geohash distorts near poles)
  - Efficient range queries using Hilbert curve index
  - Uber uses S2 for dispatch, surge pricing, geofencing

Rider requests a ride at (lat, lon):
  1. Compute S2 cell at level 14 (830m grid)
  2. Query Redis for available drivers in cell + 8 neighbours
  3. Sort by actual Euclidean distance, return top 10
```

## Partitioning the Geo Index

```
One global Redis key "drivers" doesn't scale:
  100K+ drivers → single-threaded Redis bottleneck

Partition by city:
  GEOADD drivers:san_francisco ...
  GEOADD drivers:new_york ...

Or by S2 cell at level 10 (~10 km resolution):
  GEOADD drivers:cell:{s2_l10} ...
  On ride request: query cell + neighbours (9 cells max)
```

## Update Frequency

```
GPS update: every 4 seconds per driver
500K active drivers: 500K / 4 = 125K Redis GEOADD/sec

Redis GEOADD throughput: ~100K ops/sec per node
→ Need 2-3 Redis instances for geo index

Optimisation: only update Redis if driver moved > 50m
  Reduces updates by ~60% for drivers stuck in traffic
```
