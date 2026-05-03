# Cache Tiers

Caches can exist in several layers, and each layer solves a different latency problem.

## Common Tiers

- client cache
- CDN cache
- API gateway cache
- application cache
- database cache or buffer pool

## Why This Matters

Earlier caches reduce load before requests reach deeper infrastructure.

## Real-World Analogy

Think of cache tiers as storing the same useful tool in your pocket, on your desk, in your room, and in the building supply closet.

## Trade-Offs

- Higher-level caches save more downstream work.
- More tiers create more invalidation complexity.

## Interview Use

Do not just say "use Redis." Say where caching belongs in the request path.
