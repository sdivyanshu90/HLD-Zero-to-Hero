# Redis vs Memcached

Redis and Memcached are both in-memory systems, but they are built for different levels of capability.

## Memcached

Memcached is a simpler distributed memory cache focused on key-value storage and high speed.

## Redis

Redis supports richer data structures, persistence options, replication, Lua scripting, and more operational features.

## Real-World Analogy

Memcached is a fast shelf. Redis is a fast shelf plus drawers, timers, notebooks, and some recovery tools.

## Trade-Offs

- Memcached is lighter and simpler.
- Redis is more capable but more operationally involved.

## Interview Use

Choose Redis when you need richer semantics such as sorted sets, atomic scripts, or durable-ish behavior. Choose Memcached when simple ephemeral caching is enough.
