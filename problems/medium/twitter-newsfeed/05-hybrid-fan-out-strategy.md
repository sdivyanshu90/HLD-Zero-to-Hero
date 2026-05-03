# Step 5 — Hybrid Fan-Out Strategy

## Problem: The Celebrity (Hot Write) Problem

```
Katy Perry (100 M followers) tweets.
Fan-out-on-write: 100 M Redis writes × ~200 B = 20 GB data
Time to complete: 100 M / 50 K writes/sec = 2000 seconds!

Solution: Fan-out-on-read for users with > 10 K followers
```

## Hybrid Algorithm

```
On tweet creation:
  follower_count = get_follower_count(author_id)
  
  if follower_count <= CELEBRITY_THRESHOLD:  # e.g., 10 K
    # Fan-out-on-write: push tweet_id to all follower feeds
    followers = get_followers(author_id)  # fetch from graph DB
    for follower_id in followers:
        redis.zadd(f"feed:{follower_id}", {tweet_id: timestamp})
        redis.zremrangebyrank(f"feed:{follower_id}", 0, -MAX_FEED_SIZE - 1)
    
  else:
    # Celebrity: only write to own tweet list
    redis.zadd(f"tweets:{author_id}", {tweet_id: timestamp})
    # Followers will merge this on read
```

## Read (Feed Retrieval) Algorithm

```python
def get_home_feed(user_id: int, limit: int = 20) -> List[Tweet]:
    # 1. Get pre-computed feed (fan-out-on-write users)
    feed_tweet_ids = redis.zrevrange(f"feed:{user_id}", 0, limit - 1)
    
    # 2. Get celebrity tweets (fan-out-on-read)
    followed_celebrities = get_followed_celebrities(user_id)
    # (celebrities the user follows, cached per user, 1h TTL)
    
    celebrity_tweet_ids = []
    for celeb_id in followed_celebrities:
        ids = redis.zrevrange(f"tweets:{celeb_id}", 0, limit - 1)
        celebrity_tweet_ids.extend(ids)
    
    # 3. Merge + sort by timestamp (k-way merge)
    all_ids = merge_by_score(feed_tweet_ids, celebrity_tweet_ids)[:limit]
    
    # 4. Hydrate tweets from tweet DB
    return tweet_db.mget(all_ids)
```

## Fan-Out Throughput Math

```
100 M tweets/day = 1157 tweets/sec
Average followers per user: 100
Fan-out writes: 1157 × 100 = 115 700 Redis writes/sec
Redis throughput: ~200 K ops/sec/node → 1 node sufficient for avg case
Peak (10× spike): 1.16 M writes/sec → 6 Redis nodes

Celebrity exclusion: top 0.01% of users (30K accounts) excluded from write fan-out
Reduces worst-case fan-out by ~1000×
```

## Feed ZSET Structure

```
Redis ZSET: feed:{user_id}
  member = tweet_id (string or int64)
  score  = timestamp in milliseconds

Operations:
  ZADD feed:u123 1714694400000 tweet_id_999
  ZREVRANGE feed:u123 0 19        → top 20 tweet IDs
  ZREMRANGEBYRANK feed:u123 0 -801 → trim to 800 entries

TTL: EXPIRE feed:u123 172800 (48h, refreshed on access)
Memory: 800 tweets × (8B score + 8B member) ≈ 12 KB per user
        50 M users × 12 KB = 600 GB total (need Redis cluster)
```
