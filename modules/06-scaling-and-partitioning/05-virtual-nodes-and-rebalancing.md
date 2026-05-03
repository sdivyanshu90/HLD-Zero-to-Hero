# Virtual Nodes and Rebalancing

Virtual nodes divide each physical machine into many smaller positions on the hash ring.

## Why Virtual Nodes Help

- smoother load distribution
- easier balancing across unequal hardware
- simpler recovery after node loss

## Rebalancing

Rebalancing is the process of moving ownership when nodes join, leave, or are resized.

## Real-World Analogy

Instead of giving each warehouse one giant territory, you split the map into many districts and assign many districts to each warehouse.

## Trade-Offs

- Better balance and lower shock during topology change.
- More metadata and movement planning.

## Interview Use

Mention virtual nodes when you discuss consistent hashing seriously. They are how the ring becomes practical in production.
