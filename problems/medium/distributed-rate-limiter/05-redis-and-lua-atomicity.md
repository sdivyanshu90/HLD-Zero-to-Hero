# Step 5 — Redis and Lua Atomicity

## Why Lua? The Race Condition Problem

```
Thread A: GET rl:user:123:min → 99 (under limit)
Thread B: GET rl:user:123:min → 99 (under limit)
Thread A: SET rl:user:123:min 100  ✓
Thread B: SET rl:user:123:min 100  ✓ ← both allowed! limit violated
```

Lua scripts execute atomically inside Redis (single-threaded interpreter):

## Sliding Window Counter in Lua

```lua
-- KEYS[1] = current window key
-- KEYS[2] = previous window key
-- ARGV[1] = limit
-- ARGV[2] = current window elapsed fraction (0.0-1.0)

local curr = tonumber(redis.call('GET', KEYS[1])) or 0
local prev = tonumber(redis.call('GET', KEYS[2])) or 0
local limit = tonumber(ARGV[1])
local fraction = tonumber(ARGV[2])

local weighted = curr + prev * (1 - fraction)

if weighted < limit then
    redis.call('INCR', KEYS[1])
    redis.call('EXPIRE', KEYS[1], 120)  -- 2 window TTL
    return {1, limit - curr - 1}        -- {allowed, remaining}
else
    return {0, 0}
end
```

## Token Bucket in Lua

```lua
-- KEYS[1] = bucket key
-- ARGV[1] = capacity, ARGV[2] = refill_rate, ARGV[3] = now_ms

local data = redis.call('HMGET', KEYS[1], 'tokens', 'last_ts')
local tokens   = tonumber(data[1]) or tonumber(ARGV[1])
local last_ts  = tonumber(data[2]) or tonumber(ARGV[3])

local elapsed  = (tonumber(ARGV[3]) - last_ts) / 1000.0
local capacity = tonumber(ARGV[1])
local rate     = tonumber(ARGV[2])

tokens = math.min(capacity, tokens + elapsed * rate)

if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', KEYS[1], 'tokens', tokens, 'last_ts', ARGV[3])
    redis.call('EXPIRE', KEYS[1], math.ceil(capacity / rate) + 1)
    return {1, math.floor(tokens)}
else
    return {0, 0}
end
```

## Redis Pipeline for Low Latency

```python
pipe = redis.pipeline(transaction=False)
pipe.eval(LUA_SCRIPT, 2, curr_key, prev_key, limit, fraction)
pipe.execute()
```

Single round-trip; Lua script executes atomically server-side.

## Redis Cluster Consideration

```
Lua scripts must access keys on the same slot.
Use hash tags to co-locate:
  {user:12345}:curr_min
  {user:12345}:prev_min
  → both hash to same slot (CRC16 of "user:12345")
```
