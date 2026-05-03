# Cheat Sheet: Food Delivery Platform

## Scale (BoE)
```
Orders per day: 10M (DoorDash scale)
Concurrent active orders (preparation + delivery): 200K
Concurrent delivery drivers: 500K
Location updates per driver: every 5 seconds
Location update QPS: 500K / 5 = 100K GPS writes/second
Order matching QPS: 10M / 86,400 ≈ 115 order assignments/second
```

## Order Lifecycle

```
User orders ──▶ Order Service
  │
  ├── 1. Validate restaurant open + items available (menu service)
  ├── 2. Create order record in DB (PENDING)
  ├── 3. Charge payment (payment service)
  ├── 4. Notify restaurant (push notification / tablet)
  ├── 5. Assign delivery driver (matching service)
  │         ↕ real-time location tracking (WebSocket/SSE)
  ├── 6. Driver picks up food (order status: PICKED_UP)
  ├── 7. Driver delivers food (order status: DELIVERED)
  └── 8. Trigger post-order: rating prompt, receipt email
```

## ETA Calculation

```
Two components:
  1. Food preparation ETA: historical prep time per restaurant per item
     ML model: restaurant_id × time_of_day × current_queue → prep_minutes
     
  2. Delivery ETA: routing graph with real-time traffic
     Input: driver location, restaurant location, delivery address
     Use: Google Maps / OSRM (open-source routing machine)
     = drive_time(driver → restaurant) + drive_time(restaurant → delivery)
     
  Live ETA update:
     As driver moves → recalculate ETA every 30 seconds
     Push update via WebSocket to user's app
```

## Geospatial Matching

```
Find best driver for order:
  1. Geo query: find all available drivers within 5 km of restaurant
     Redis GEORADIUS drivers:available {restaurant_lat} {restaurant_lon} 5 km
  
  2. Rank candidates:
     Score = α × distance + β × expected_wait + γ × driver_rating
  
  3. Offer to best candidate (timeout: 30 seconds)
     If declined/timeout → offer to next candidate
  
  4. Once accepted: assign driver to order (DB update + notify driver)
  
Driver state machine:
  OFFLINE → ONLINE (available) → BUSY (picking up / delivering) → ONLINE
  Redis SET: driver:{id}:status → ONLINE/BUSY/OFFLINE
```

## Bottlenecks
1. Real-time order tracking: 200K active orders × user polling → WebSocket > polling
2. Surge pricing: similar to Uber → count available drivers vs active orders per geo cell
3. Restaurant capacity: can only handle N orders simultaneously → order throttling per restaurant

## Unique Trick
Batched driver-to-order matching: instead of assigning each order immediately on arrival, batch 30-60 seconds of orders and solve them together as an optimization problem (minimize total delivery time across all assignments). Better global optimum than greedy one-by-one assignment.
