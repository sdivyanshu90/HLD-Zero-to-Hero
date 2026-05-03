# Cheat Sheet: Service Discovery and Config

## Scale (BoE)
```
Services: 500 microservices
Instances per service: 3-50 replicas
Total instances: ~5,000 service instances
Config updates per day: 100 (small frequent changes)
Health check QPS: 5,000 instances × 1 check/10s = 500 health checks/second
Discovery queries: 500 services × 10K QPS inter-service calls = need sub-millisecond lookup
```

## System Diagram
```
Service A starts ──▶ Register with Consul
                     {service: "payment", id: "payment-1", address: "10.0.1.50", port: 8080}
                           │
                     Consul stores in Raft cluster (3-5 nodes)
                           │
Service B wants to call payment service:
  Query Consul DNS: payment.service.consul → [10.0.1.50, 10.0.1.51, 10.0.1.52]
  Client-side LB: pick one → connect
```

## Service Registration and Health Checks

```
Registration:
  Service registers on startup with Consul agent (local sidecar)
  Consul agent: forwards registration to Consul cluster (Raft)
  
  Health check types:
    HTTP: GET /health → expect 200 (most common)
    TCP: connect to port → success = open
    Script: run command → exit 0 = healthy
    TTL: service must renew TTL every N seconds or marked unhealthy
  
  Deregistration:
    On graceful shutdown: service deregisters itself
    On crash: health check fails 3 times → Consul removes instance
    Kubernetes: integration via consul-k8s, auto-registers pods
```

## Distributed Configuration

```
Problem: 500 services × 50 config values = 25,000 config entries
  Feature flags, DB connection strings, rate limits, etc.
  
  Config store: Consul KV or etcd (Raft-based, strongly consistent)
  
  Key hierarchy:
    /config/production/payment-service/db_host = "db-1.internal"
    /config/production/payment-service/rate_limit_qps = "10000"
    /config/global/feature_flags/new_checkout = "true"
  
  Watch for changes:
    Services watch their config keys (long poll)
    On change: callback triggered → reload config without restart
    → Feature flags toggle: 0 to 100% rollout by updating /feature_flags/
    
  etcd watch:
    etcdctl watch /config/payment-service/ --recursive
    → Get notified on any change under that prefix
```

## Leader Election

```
Use case: scheduled job should run on exactly ONE instance (not all 3 replicas)
  
  Leader election via distributed lock:
    All instances try: etcd.put("/leader/job_X", "instance-1", lease=30s)
    (only one can win IF key doesn't exist)
    Winner: runs the job, renews lease every 10s
    Others: watch key, take over if lease expires
    
    This is the same Raft consensus used internally by etcd/Consul!
```

## Unique Trick
Consul's catalog (service registry) and health checks are integrated with its DNS interface. Services discover peers via DNS lookup (payment.service.consul) — no code changes needed, works with any language/framework. Under the hood, Consul uses Raft for strong consistency across its 3-5 node cluster, ensuring every service sees the same service catalog.
