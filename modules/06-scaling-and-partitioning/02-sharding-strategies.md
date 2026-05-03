# Sharding Strategies

## What Is Sharding?

Sharding (horizontal partitioning) splits a large dataset across multiple database instances (shards) such that each shard holds a disjoint subset of the data.

```
Without sharding:                With sharding (4 shards):
                                 
┌──────────────────────┐         Shard 0: user IDs 0-24M
│  users table         │    →    Shard 1: user IDs 25-49M
│  100M rows           │         Shard 2: user IDs 50-74M
│  1 machine           │         Shard 3: user IDs 75-99M
└──────────────────────┘
  Too slow, too big!             Each shard: 25M rows, manageable!
```

---

## Sharding Strategy 1: Range-Based Sharding

Divide data by contiguous ranges of a key:

```
User ID range sharding:
  Shard 0:  user_id 0        – 24,999,999
  Shard 1:  user_id 25,000,000 – 49,999,999
  Shard 2:  user_id 50,000,000 – 74,999,999
  Shard 3:  user_id 75,000,000 – 99,999,999

Time-based range sharding:
  Shard Jan: created_at 2024-01-01 – 2024-01-31
  Shard Feb: created_at 2024-02-01 – 2024-02-28
  ...

Advantages:
  ✓ Range queries on shard key are efficient (scan one shard)
  ✓ Natural partitioning for time-series data
  ✓ Easy to understand and reason about

Disadvantages:
  ✗ Hotspot problem: all new writes go to the "latest" shard
     (all January traffic hits Shard Jan until February)
  ✗ Uneven load if key distribution is non-uniform
     (power users generate more data → one shard gets more load)
  ✗ Manual rebalancing when shards fill up
```

### Range Sharding Hotspot Fix

```
Salting: add random prefix to range-shard key

Instead of: key = order_id
Use:        key = random(0-9) + order_id

Shard assignment: key[:1] % num_shards → distributes randomly within range

Cost: range queries now require scatter-gather to all shards
      But write throughput is even across all shards
```

---

## Sharding Strategy 2: Hash-Based Sharding

Apply a hash function to the shard key to distribute data uniformly:

```
Hash sharding:
  shard = hash(user_id) % num_shards

  user_id=1234:   hash(1234) % 4 = 2  → Shard 2
  user_id=5678:   hash(5678) % 4 = 1  → Shard 1
  user_id=9999:   hash(9999) % 4 = 3  → Shard 3

Advantages:
  ✓ Even distribution of data across all shards
  ✓ No hotspots (assuming good hash function)
  ✓ Simple to implement

Disadvantages:
  ✗ Range queries require scatter-gather to ALL shards
     SELECT * FROM orders WHERE user_id BETWEEN 1000 AND 2000;
     → Must query all 4 shards (don't know which shards have user IDs in range)
  ✗ Rebalancing nightmare:
     When adding Shard 5: hash(user_id) % 5 ≠ hash(user_id) % 4
     → Almost all data must be moved! (4/5 = 80% of data remapped)
     → Consistent hashing solves this
```

---

## Sharding Strategy 3: Directory-Based Sharding

A lookup table maps each entity to its shard:

```
Shard directory table:
  user_id  → shard_id
  1        → shard_2
  2        → shard_0
  3        → shard_1
  ...

Advantages:
  ✓ Flexible: can move individual users between shards
  ✓ Non-uniform distribution possible (put VIP users on dedicated shards)
  ✓ Easy rebalancing: just update the directory table

Disadvantages:
  ✗ Single point of failure: directory service must be highly available
  ✗ Extra network hop on every request (directory lookup)
  ✗ Directory itself can become a bottleneck (must cache aggressively)
  ✗ Directory table grows large for large datasets
```

---

## Sharding Complications

### Cross-Shard Queries

```
User on Shard 2, orders on Shard 1:
  SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id
  WHERE u.id = 1234;

  Problem: u.id=1234 is on Shard 2, o records are on Shard 1
  Solutions:
  
  1. Scatter-gather: query both shards, join in application
     Cost: 2 network round trips, application-side join

  2. Co-locate: ensure user and their orders are on the same shard
     user_id=1234 → Shard 2
     orders with user_id=1234 → also Shard 2 (same hash)
     Use user_id as shard key for BOTH tables!

  3. Denormalize: copy user data into orders table
     orders.user_name = "Alice" (duplicated, not normalized)
     Eliminates cross-shard join at cost of data duplication
```

### Cross-Shard Transactions

```
Transfer $100 from user on Shard A to user on Shard B:
  BEGIN transaction on Shard A
  BEGIN transaction on Shard B
  Deduct $100 from account on Shard A
  Add $100 to account on Shard B
  ???

  Two-Phase Commit (2PC):
    Phase 1 (Prepare): coordinator asks both shards "can you commit?"
    Phase 2 (Commit): if both say yes → commit; if either says no → rollback
    
    Problem: coordinator can fail between phase 1 and phase 2
    → Shards are left in uncertain state ("in doubt" transaction)
    → Blocks rows indefinitely until coordinator recovers
    
    2PC is notorious for availability issues

  SAGA Pattern:
    Sequence of local transactions with compensating transactions
    Step 1: deduct $100 from Shard A (local ACID transaction)
    Step 2: add $100 to Shard B (local ACID transaction)
    If Step 2 fails: compensating transaction: add $100 back to Shard A
    
    Eventually consistent, but no blocking on coordinator failure
    Used by microservices and distributed databases
```

---

## Choosing a Shard Key

The shard key is the most important decision in sharding. Bad choices cause hotspots, poor performance, and expensive migrations.

```
Good shard key properties:
  1. High cardinality: many distinct values (not boolean, not low-enum)
  2. Even distribution: uniform frequency across values
  3. Aligned with access patterns: co-locate data accessed together
  4. Immutable: never changes (user_id > email address, which can change)
  5. Not monotonically increasing: avoid range hotspots (UUID > auto-increment)

Bad shard keys:
  ✗ status (active/inactive): only 2 values → all data on 2 shards
  ✗ created_at (time): monotonically increasing → all writes to latest shard
  ✗ country (US gets 30% of traffic): uneven → US shard is hotspot
  ✗ email (changes): requires expensive data migration when email changes

Good shard keys:
  ✓ user_id (UUID or high-cardinality int): uniform, immutable
  ✓ order_id (hash): uniform
  ✓ tenant_id (SaaS multi-tenant): ensures one tenant = one shard
```

---

## Interview Quick Answers

- **What is the biggest problem with simple hash sharding?** — Rebalancing. When you add a shard, `hash(key) % N` changes for nearly all keys (at least (N-1)/N fraction). This requires moving almost all data to new shards. Consistent hashing solves this.
- **Why is time (created_at) a bad shard key?** — Monotonically increasing values create a "hot" latest shard. All new writes go to the shard handling the most recent time range. The other shards are cold (only serving reads). Use a hash or add a random prefix if you need time-based range queries.
- **How do you handle a cross-shard join?** — Option 1: co-locate related data on the same shard (user and their orders share the same user_id shard key). Option 2: scatter-gather and join in the application tier. Option 3: denormalize (embed data from one table into the other to eliminate the join).
