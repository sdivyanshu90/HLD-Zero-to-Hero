# Step 8 — Checkpoint & Interview Q&A

**Q1: How do you assign a courier to an order within 60 seconds?**
> When an order enters READY_FOR_PICKUP state, dispatch service runs GEORADIUS for available couriers within 5 km (Redis GEO). Ranks by: distance, estimated travel time (route graph), courier rating. Sends push notification to top-3 couriers simultaneously. First to accept is assigned (atomic Redis SET NX on courier_id). If none accept in 30s, expand radius and retry.

**Q2: How do you calculate accurate ETA?**
> Two-component ETA: (1) Prep time: ML model trained on restaurant's historical prep times, current queue depth, item complexity. (2) Delivery time: Dijkstra / A* on road graph with real-time traffic (Google Maps API or OSM). ETA = max(prep_ready_time, courier_arrival_time) + delivery_time. Update ETA every 60 seconds as order progresses.

**Q3: How do you handle the saga for order creation (DB + payment + restaurant notification)?**
> Choreography-based saga with Kafka: (1) ORDER_CREATED event triggers payment service. (2) PAYMENT_COMPLETED triggers order confirmation + restaurant notification. (3) PAYMENT_FAILED triggers ORDER_CANCELLED compensating transaction. Each step is idempotent (order_id as idempotency key). Rollback: send REFUND event if any downstream step fails.

**Q4: How do you scale the menu catalog for millions of concurrent browse requests?**
> Menus are read-heavy and change infrequently (updated by restaurants occasionally). Cache full menu JSON in Redis per restaurant (TTL 10 min). On menu update by restaurant, invalidate Redis key (event-driven via webhook). CDN caches menu responses at edge for static content. With Redis absorbing 95% of reads, DB only handles cache misses.

**Q5: How do you handle a courier going offline mid-delivery?**
> Monitor courier GPS heartbeat (update every 30s). If no heartbeat for > 2 minutes: (1) Alert customer (estimated delay). (2) If order hasn't been picked up: re-assign to another courier. (3) If order picked up: mark as potentially delayed, alert ops team. (4) When courier reconnects: resume tracking normally. Insurance/compensation handled by ops if delivery fails.
