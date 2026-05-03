# Cache Failures

Caching failures are often harder than cache hits are easy.

## Cache Stampede

Many clients miss the same hot key and all hit the origin at once.

## Cache Penetration

Repeated requests for missing data bypass the cache and hammer the database.

## Cache Invalidation

The system serves stale data because updates and cache refresh do not line up correctly.

## Real-World Analogy

A stampede is everyone rushing to the same service desk at once. Penetration is people repeatedly asking for a product that does not exist. Invalidation is outdated notices still hanging in every hallway.

## Trade-Offs

- Aggressive caching improves speed.
- It increases correctness risk and failure amplification if invalidation is weak.

## Interview Use

Whenever you add a cache, say how you will handle stampede, misses for nonexistent keys, and invalidation.
