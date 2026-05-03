# Shard Key Selection

## The Most Important Sharding Decision

The shard key determines data distribution, access patterns, and cross-shard complexity. A bad shard key creates hotspots that bottleneck your entire system. Fixing a bad shard key later is extremely expensive.

---

## Properties of an Ideal Shard Key

```
1. High cardinality
   → Many distinct values (millions+)
   → Bad: status (2 values), country (200 values)
   → Good: user_id (millions), order_id (billions)

2. Even distribution
   → Similar frequency for each shard key value
   → Bad: Pareto-distributed data (top 1% users generate 80% of requests)
   → Good: uniformly distributed UUIDs or hashed integers

3. Aligned with access patterns
   → Co-locate data that's accessed together
   → User + their posts on the same shard → no cross-shard JOINs
   → Bad: shard posts by post_id (random) when queries are "user's posts"

4. Immutability
   → Shard key should never change
   → Bad: email (users change email) → data must be moved to new shard
   → Good: user_id (assigned once, never changes)

5. Low hotspot risk
   → Monotonically increasing keys create sequential hotspots
   → Auto-increment IDs: all new inserts go to the "max" shard
   → Use: UUID v4, hash(auto_increment_id), timestamp + random suffix
```

---

## Shard Key Examples by System Type

### Social Network (Posts, Comments, Likes)

```
Option 1: Shard by post_id
  Post queries: fast (post_id → direct shard lookup)
  "Get all posts by user X": scatter-gather to all shards!
  
Option 2: Shard by user_id (recommended)
  User's posts: all on same shard → fast
  Single post by ID: include user_id in URL/request → direct lookup
  
  URL structure: twitter.com/alice/status/1234
                 (user=alice → shard → look for status 1234 there)

  Social graph (followers/following): also on same shard as user
  → Most operations for "user X's timeline": hits 1 shard

Compromise pattern: "locality-aware shard key"
  Store user content (posts, comments, likes) on the user's shard
  Include user_id as prefix in content IDs
  content_id = user_id + sequence  →  shard(content_id) = shard(user_id)
```

### E-Commerce (Orders, Products)

```
Option 1: Shard by order_id
  Order lookup: fast
  "All orders by customer X": scatter-gather!

Option 2: Shard by customer_id (recommended for OLTP)
  Customer's order history: all on same shard
  Inventory: separate, possibly by product_category_id
  
  Challenge: customer A has 10,000 orders, customer B has 1 order
  → Customer A's shard has 10,000× more data for that customer
  → Use tenant-aware sharding with fixed-size shards + customer migration

Option 3: Time-based sharding (for analytics)
  Recent orders: hot shard
  Old orders: cold shards
  Good for data lifecycle (archive old orders automatically)
  Bad for write hotspots (all writes to current month's shard)
```

### Multi-Tenant SaaS

```
Shard by tenant_id:
  All data for Tenant A on Shard 1
  All data for Tenant B on Shard 2
  → Perfect isolation between tenants
  → Simple per-tenant queries (no cross-shard)
  → Easy tenant-level backup, restore, migration

Challenge: unequal tenants
  Enterprise tenant: 1,000 users, 100 GB data
  Free tenant: 1 user, 10 MB data
  → "Noisy neighbor": enterprise tenant monopolizes its shard

Solutions:
  Dedicate a shard (or multiple) to large tenants
  Shard large tenants by user_id within the tenant
  Use a hybrid: small tenants share shards, large tenants get dedicated shards
```

---

## Hotspot Mitigation Techniques

### Salting

```
Problem: trending post gets 1M reads/second, all hitting the same shard
         hash(post_id=12345) → shard 3 → shard 3 is overwhelmed

Solution: add random salt to distribute copies:
  Store N copies of the post with different key prefixes:
    key_0 = "0:" + post_id=12345
    key_1 = "1:" + post_id=12345
    ...
    key_N = "9:" + post_id=12345

  Read: random(0-9) + post_id → pick random copy
  Write: must update ALL N copies (fan-out write)
         Trade-off: N× write amplification for 1/N read hotspot

Used by: DynamoDB auto-sharding for hot partitions
```

### Composite Shard Keys

```
For time-series: bucket by user + time
  shard_key = user_id + month_bucket

  hash("user:1234:2024-01") → shard A  (Jan 2024 data for user 1234)
  hash("user:1234:2024-02") → shard B  (Feb 2024 data)

  Query "user 1234's last 30 days": 1-2 shards (current + prev month)
  Query "all Jan 2024 data": scatter-gather (but only month partitions)

  Avoids time-based hotspot: data for different users spreads to different shards
  within the same time bucket
```

---

## Re-sharding: The Expensive Migration

When your shard key was wrong and you must change it:

```
Migration process:
  1. Create new shard cluster with new key
  2. Double-write: write to BOTH old and new cluster
  3. Backfill: copy existing data from old → new cluster
  4. Verify: data in new cluster is complete and consistent
  5. Switch reads to new cluster
  6. Stop double-write, decommission old cluster

Cost: typically weeks/months of engineering for large datasets
      Requires careful handling of in-flight writes during migration
      Risk: data inconsistency between old and new

Prevention: spend time on shard key design upfront
            prototype with real production-like data and access patterns
```

---

## Interview Quick Answers

- **Why should a shard key be immutable?** — Changing a shard key value means the record must move to a different shard. This requires a delete from the old shard and an insert to the new shard, ideally atomically across shards (very hard). Email addresses change; user IDs don't. Always choose the stable identifier.
- **How do you handle a celebrity/hot key problem?** — For reads: cache the hot key aggressively (CDN or Redis). For writes: use salting (store N copies with random prefixes, write to all N, read from random one). Accept that some keys will be hot; scale that specific shard vertically or with dedicated replicas.
- **What is tenant-aware sharding?** — Multi-tenant SaaS places all data for one customer on one shard. Pros: perfect isolation, no cross-shard joins for any per-tenant query. Cons: large tenants can overwhelm their shard. Solution: give large tenants dedicated shards or shard large tenants internally by user_id.
