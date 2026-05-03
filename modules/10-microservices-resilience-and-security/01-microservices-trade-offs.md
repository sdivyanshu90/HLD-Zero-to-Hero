# Microservices Trade-offs

## Monolith vs Microservices

```
Monolith:
  All code in one deployable artifact
  
  ┌──────────────────────────────────────────┐
  │  Monolith                                 │
  │  ┌───────────┐  ┌───────────┐  ┌───────┐ │
  │  │  User     │  │  Order    │  │ Email │ │
  │  │  Service  │  │  Service  │  │Service│ │
  │  └─────┬─────┘  └─────┬─────┘  └───┬───┘ │
  │        └──────────────┼─────────────┘      │
  │              Shared DB + code               │
  └────────────────────────────────────────────┘
  
  Advantages:
    ✓ Simple deployment: one artifact
    ✓ Low operational overhead
    ✓ In-process function calls (no network latency)
    ✓ Easier transactions (same DB, ACID)
    ✓ Easy debugging (one process, one log stream)
  
  Disadvantages:
    ✗ Scaling: must scale ALL components even if only one is hot
    ✗ Technology lock-in: one language/framework
    ✗ Deployment coupling: any change requires full redeploy
    ✗ Fault coupling: one bug can crash the whole app
    ✗ Team scaling: large teams fighting over one codebase

Microservices:
  Each business capability is a separate deployable service

  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │ User        │  │ Order       │  │ Email       │
  │ Service     │  │ Service     │  │ Service     │
  │ [own DB]    │  │ [own DB]    │  │ [own DB]    │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │                │                │
         └────────────────┼────────────────┘
                    API / Message Bus
  
  Advantages:
    ✓ Independent deployability (deploy Order Service without touching Email)
    ✓ Independent scaling (scale Order Service 10× without scaling User Service)
    ✓ Technology diversity (Java for payment, Python for ML, Node for API)
    ✓ Team autonomy (each team owns their service end-to-end)
    ✓ Fault isolation (email service crash doesn't affect order service)
  
  Disadvantages:
    ✗ Distributed systems complexity (network failures, latency, partitions)
    ✗ No distributed ACID transactions (Saga pattern required)
    ✗ Service discovery (services find each other via service mesh/registry)
    ✗ Operational overhead (N services × monitoring/logging/deployment)
    ✗ Testing complexity (need to test service interactions)
```

---

## Conway's Law and Team Structure

```
Conway's Law: "Organizations design systems that mirror their communication structure"

If you have 3 teams → you'll get a 3-tier system (even if you try for microservices)

Inverse Conway Maneuver:
  Design your org structure to match the desired architecture
  If you want microservices → organize teams around business capabilities

  ┌────────────────────────────────────────────────────┐
  │   Team: Payments        Team: Catalog    Team: Orders│
  │   ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
  │   │Payment Svc  │  │Catalog API  │  │Order Svc   │ │
  │   │Payment DB   │  │Search Index │  │Order DB    │ │
  │   │Fraud Svc    │  │Image CDN    │  │Notif Svc   │ │
  │   └─────────────┘  └─────────────┘  └────────────┘ │
  └────────────────────────────────────────────────────┘
  
  Each team: full-stack ownership, their own deployment pipeline
```

---

## Service Boundaries: Domain-Driven Design

```
Bounded Context: a logical boundary within which a domain model is internally consistent

Bounded Context     Service(s)
─────────────────────────────────────────────────────
User Identity       AuthService, ProfileService
Product Catalog     CatalogService, SearchService
Orders              OrderService, CartService
Payments            PaymentService, FraudService
Fulfillment         InventoryService, ShippingService
Communications      EmailService, SMSService, PushService

Database per service:
  Each service owns its data store
  No direct DB cross-service queries!
  To access another service's data: call their API or subscribe to their events
  
  This is "polyglot persistence":
    OrderService   → PostgreSQL (relational, ACID for orders)
    CatalogService → MongoDB (flexible schema for products)
    SearchService  → Elasticsearch (full-text search)
    SessionService → Redis (fast key-value, TTL)
    EventService   → Kafka (high-throughput streaming)
```

---

## API Gateway Pattern

```
Without API Gateway:
  Client calls User Service, Order Service, Payment Service separately
  Client must know addresses of all services
  Each service implements auth, rate limiting, etc.

With API Gateway:
  ┌──────────────────────────────────────────────────┐
  │                  API Gateway                      │
  │  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
  │  │   Auth   │  │  Rate    │  │  SSL Termina-  │  │
  │  │  (JWT)   │  │ Limiting │  │     tion       │  │
  │  └──────────┘  └──────────┘  └───────────────┘   │
  └──────────────────────────────────────────────────┘
           │           │             │
     ┌─────┘     ┌─────┘       ┌────┘
     ▼           ▼             ▼
  User Svc   Order Svc     Payment Svc

API Gateway responsibilities:
  - Request routing to correct service
  - Authentication/authorization (validate JWT)
  - Rate limiting (per user or per client)
  - Request/response transformation
  - SSL termination
  - Request aggregation (BFF pattern)

BFF (Backend for Frontend):
  Separate API gateway per client type:
    Mobile BFF → aggregates multiple calls for mobile-optimized responses
    Web BFF → different aggregation for web app
    Partner BFF → filtered, rate-limited view for API partners
```

---

## Interview Quick Answers

- **When should you NOT use microservices?** — Early-stage startup (premature optimization, high operational overhead with small team), when team size doesn't justify it (2-pizza rule: need a team per service), when you don't have a strong DevOps culture (microservices require CI/CD, container orchestration, distributed tracing).
- **How do microservices communicate?** — Synchronous: REST/HTTP or gRPC for request-response. Asynchronous: message queues/Kafka for event-driven. Rule: use async when the calling service doesn't need an immediate response (order confirmation → send email via queue). Use sync for immediate responses (get user profile).
