# Service Discovery and Service Mesh

## The Problem: How Do Services Find Each Other?

```
Microservices: 50 services, each deployed as 3 replicas, IP changes on every restart

Without service discovery:
  order-service config:
    payment_service_url = "http://10.0.1.50:8080"  ← hardcoded!
    ← what if IP changes? → broken!
    ← which of the 3 replicas? → no load balancing!
```

---

## Service Registry

A central directory that tracks which services are running and where:

```
               ┌─────────────────────────┐
               │    Service Registry      │
               │  (Consul / Eureka / etcd) │
               │                           │
               │  payment-service:         │
               │    10.0.1.50:8080         │
               │    10.0.1.51:8080         │
               │    10.0.1.52:8080         │
               └─────────────────────────┘
                    ▲             ▲
               register       register
                    │             │
              payment:50     payment:51

  order-service wants to call payment-service:
    1. Lookup "payment-service" in registry
    2. Get list: [10.0.1.50:8080, 10.0.1.51:8080, 10.0.1.52:8080]
    3. Load balance: pick one (round-robin, random, least-connections)
    4. Make request
```

### Client-Side vs Server-Side Discovery

```
Client-side discovery (Eureka):
  Each service has a Eureka client library
  Client queries Eureka registry directly
  Client does load balancing (Ribbon)
  
  ┌─────────────┐         ┌─────────────┐
  │Order Service│──query──▶│Eureka Server│
  │             │◄─list────│             │
  │ pick one ──────────────────────────────▶ Payment (50)
  └─────────────┘         └─────────────┘

  ✓ No extra hop (client connects directly)
  ✗ Every language/framework needs a service registry client
  ✗ Load balancing logic distributed across all services

Server-side discovery (Consul + load balancer):
  Client sends request to load balancer
  Load balancer queries registry, forwards to instance
  
  ┌─────────────┐      ┌────────────┐    ┌─────────────┐
  │Order Service│─────▶│  LB/Proxy   │───▶│Payment (50) │
  └─────────────┘      │ (HAProxy    │    └─────────────┘
                       │ or Envoy)   │
                       │  ─consults──▶   Consul Registry
                       └────────────┘
  
  ✓ Service is registry-agnostic (no client library per language)
  ✓ Centralized load balancing and discovery logic
  ✗ Extra network hop
```

---

## Service Mesh

Service mesh: per-service sidecar proxies that handle all inter-service communication:

```
Without service mesh:
  Each service implements: auth, TLS, retries, circuit breakers, tracing
  → Repeated in every service, in every language

With service mesh (Istio / Linkerd):
  ┌─────────────────────────────────────────────────────┐
  │ Order Service Pod                                    │
  │  ┌──────────────────┐   ┌──────────────────────┐    │
  │  │ Order Service    │◄──▶│ Envoy sidecar proxy  │    │
  │  │ (app code)       │   │ (handles: mTLS, retry,│    │
  │  └──────────────────┘   │  circuit breaker,     │    │
  │                          │  tracing, metrics)   │    │
  │                          └──────────────────────┘    │
  └─────────────────────────────────────────────────────┘
           │ (all traffic through sidecar)
           ▼
  ┌─────────────────────────────────────────────────────┐
  │ Payment Service Pod                                  │
  │  ┌──────────────────┐   ┌──────────────────────┐    │
  │  │ Payment Service  │◄──▶│ Envoy sidecar proxy  │    │
  │  │ (app code)       │   └──────────────────────┘    │
  │  └──────────────────┘                               │
  └─────────────────────────────────────────────────────┘

Sidecar handles:
  ✓ mTLS: mutual TLS between all services (authentication + encryption)
  ✓ Retries and timeouts (configured in policy, not in code)
  ✓ Circuit breaking (configured in policy)
  ✓ Distributed tracing (injects trace headers, reports spans)
  ✓ Load balancing (across service instances)
  ✓ Traffic shaping (canary: 10% to v2, 90% to v1)
  
  App code is decoupled from all of this!
  Switch from no-retry to retry: change YAML config, not code

Control plane (Istio Pilot):
  Distributes configuration to all Envoy sidecars
  Configures: routing rules, policies, certificates
  Observability: collects telemetry from all sidecars
```

---

## Health Checks

```
Types of health checks:

  Liveness probe: is the process alive?
    If fails: container is restarted
    Check: simple HTTP 200 or process is running
    
  Readiness probe: is the service ready to accept traffic?
    If fails: service removed from load balancer rotation
    Check: can connect to DB, downstream dependencies healthy
    
  Startup probe: has the app finished starting up?
    For slow-starting apps: prevents liveness check from killing app during startup

Kubernetes probes:
  livenessProbe:
    httpGet:
      path: /health/live
      port: 8080
    initialDelaySeconds: 10
    periodSeconds: 10
    failureThreshold: 3  # restart after 3 consecutive failures
  
  readinessProbe:
    httpGet:
      path: /health/ready
      port: 8080
    periodSeconds: 5
    failureThreshold: 1  # remove from LB after 1 failure (conservative)
```

---

## Interview Quick Answers

- **What is the difference between client-side and server-side service discovery?** — Client-side: the calling service queries the registry directly and picks an instance (library in each service, e.g., Eureka + Ribbon). Server-side: the calling service hits a load balancer that handles registry lookup and forwarding (no registry knowledge in calling service, e.g., Consul + HAProxy).
- **What does a service mesh add over basic service discovery?** — Service mesh provides: mTLS between services (zero-trust), retry/circuit breaker policies (configured not coded), distributed tracing, traffic shaping (canary deploys), and centralized observability — all via sidecar proxy without touching application code.
