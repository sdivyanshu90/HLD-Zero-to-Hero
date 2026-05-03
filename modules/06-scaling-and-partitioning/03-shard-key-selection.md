# Shard Key Selection

The shard key controls distribution, routing simplicity, and how often queries need to fan out across shards.

## Good Shard Keys

Good shard keys:

- spread load reasonably evenly
- align with dominant access patterns
- reduce cross-shard operations

## Bad Shard Keys

Bad shard keys:

- create hot partitions
- force many fan-out reads
- make rebalancing painful

## Real-World Analogy

Choosing a shard key is like deciding the postal code system for a country. If the map is badly divided, every delivery route becomes expensive.

## Trade-Offs

- Uniform distribution may hurt locality.
- Strong locality may create hot spots.

## Interview Use

If you cannot defend the shard key, the design is not yet stable.
