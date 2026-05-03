# Step 8 — Checkpoint & Interview Q&A

**Q1: How do you find nearby available drivers efficiently?**
> Redis GEO (GEOADD / GEORADIUS) stores driver locations as geohash-encoded sorted set members. GEORADIUS runs a bounding-box query internally and computes distances in O(N+log M) where N = results, M = total drivers. For 500K drivers, this completes in < 5ms. Partition the geo index by city or S2 cell to distribute load.

**Q2: How do you handle 200K GPS updates per second?**
> GPS updates hit a Location Service tier that writes to Redis GEO (current state) and Kafka (event stream). Redis GEO acts as a mutable current-position store. Kafka stores immutable GPS history for trip replays and analytics. Skip Redis update if driver moved < 50m to reduce write volume by ~60%.

**Q3: How does surge pricing work architecturally?**
> A Flink/Kafka Streams job consumes real-time demand (ride requests) and supply (available driver locations) events. For each S2 cell at level 12 (~3 km), it computes demand/supply ratio every 60 seconds. If ratio > threshold (e.g., 2.0), surge multiplier increases. Published to a config store (Redis/etcd); rider app reads surge multiplier when requesting a ride.

**Q4: How do you match a rider to the best driver?**
> GEORADIUS returns N nearby available drivers sorted by distance. Apply filters: driver rating, car type, availability status. Optionally run ETA estimation (route graph: A* or Dijkstra). Send the ride request to the best match via push notification. If driver rejects/times out, move to next candidate. All within a 5-second SLA.

**Q5: What's the consistency model for driver location data?**
> Eventual consistency is acceptable. If driver location is 4-8 seconds stale, the matching algorithm still works correctly — accuracy within 100m is sufficient. The critical guarantee is no double-booking (a driver assigned to one trip doesn't receive a second match), enforced by setting driver status to IN_TRIP atomically in Redis + DB.
