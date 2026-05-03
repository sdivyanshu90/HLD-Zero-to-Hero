# Cheat Sheet: Twitter Newsfeed

## Scale (BoE)
```
DAU: 300M
Tweets per day: 500M (300M users × ~1.67 tweets/day average)
Write QPS: 500M / 86,400 ≈ 5,800 WPS
Feed reads: 300M × 20 refreshes/day / 86,400 ≈ 70K RPS read
Follows: avg user follows 200 people → fan-out write to 200 feeds per tweet
Fan-out write QPS: 5,800 × 200 = 1.16M Redis writes/second
```

## Fan-Out Strategies

```
Fan-out on WRITE (push model):
  When user A tweets → push tweet to ALL followers' feed caches
  User B opens app → just read pre-computed feed from cache (fast!)
  
  ✓ Feed read is O(1) (just read pre-filled list)
  ✗ Fan-out write is O(followers) → celebrities with 10M followers = 10M Redis writes per tweet!

Fan-out on READ (pull model):
  When user B opens app → fetch tweets from all N people they follow (union)
  → Sort by time → show feed
  
  ✓ No fan-out write overhead
  ✗ Feed read is expensive: O(followed_users) → N DB queries or sorted set unions

Hybrid (Twitter's actual approach):
  Regular users (< 10K followers): fan-out on WRITE → pre-compute feed
  Celebrities (> 10K followers): fan-out on READ → merge at read time
  Hot content: cache popular tweets independently
```

## System Diagram
```
User tweets ──▶ Tweet Service ──▶ DB (tweets table)
                    │
                    ▼ (for regular users)
               Fan-out Worker ──▶ Redis sorted set per user
                                  (feed:{user_id}: list of tweet IDs)
                    │ (celebrities: skip)
                    
User reads feed:
  1. Read feed:{user_id} from Redis (sorted set, top 200 tweet IDs)
  2. Fetch tweet details by ID from Redis/DB (hydration)
  3. For each followed celebrity: fetch latest N tweets on read
  4. Merge + sort by time → return page
```

## Key Data Model
```
tweets: (id, user_id, content, created_at, like_count, retweet_count)
follows: (follower_id, followed_id)

Redis:
  feed:{user_id}      → ZSET (tweet_id, timestamp score), max 1000 entries
  tweet:{tweet_id}    → HASH (all tweet fields, cached)
  timeline:{user_id}  → sorted set (most recent tweets from followed)
```

## Bottlenecks
1. Celebrity fan-out: skip for celebrities > 10K followers, merge on read
2. Feed read latency: solved by pre-computed sorted sets in Redis

## Unique Trick
The sorted set (ZSET) is the perfect data structure for a newsfeed: ZADD with timestamp as score, ZREVRANGE to get most recent N tweets, ZRANGEBYSCORE for time-window queries. Redis ZADD is O(log N).
