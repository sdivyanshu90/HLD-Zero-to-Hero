# Service Discovery and Config — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** Consul, etcd, Raft, health-checks, leader-election, config-push  
**Companies:** Hashicorp (Consul), CoreOS (etcd), Netflix (Eureka), AWS

---

## Problem Statement

Design a service discovery and distributed configuration system that:
- Allows services to register themselves and discover other services
- Provides health checking and automatic deregistration of failed instances
- Distributes configuration to 10,000 services in < 5 seconds
- Tolerates network partitions (CAP: CP system)

---

## Architecture Diagram

```
Services (clients)
   │  register + heartbeat   │  watch config
   ▼                         ▼
┌────────────────────────────────────────────┐
│   Service Registry Cluster (Consul/etcd)   │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│   │  Node 1  │ │  Node 2  │ │  Node 3  │  │
│   │ (leader) │ │(follower)│ │(follower)│  │
│   └──────────┘ └──────────┘ └──────────┘  │
│           Raft consensus                   │
└────────────────────────────────────────────┘
         │                │
         ▼                ▼
  Service Catalog    Config Store
  (health + IPs)    (key-value pairs)
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Registry and Heartbeats](02-registry-and-heartbeats.md)
3. [Service Discovery Read Path](03-service-discovery-read-path.md)
4. [Consensus and Leader Election](04-consensus-and-leader-election.md)
5. [Configuration Distribution](05-configuration-distribution.md)
6. [Watchers, Caching, and Failures](06-watchers-caching-and-failures.md)
7. [Split-Brain and Fencing](07-split-brain-and-fencing.md)
8. [Checkpoint](08-checkpoint.md)
