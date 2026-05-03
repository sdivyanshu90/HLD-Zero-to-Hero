# API Paradigms: REST, GraphQL, gRPC, and More

## The Four Main Paradigms

```
┌────────────────────────────────────────────────────────────────┐
│                     API PARADIGM LANDSCAPE                      │
│                                                                  │
│  REST          GraphQL          gRPC            WebSocket       │
│  ─────────     ────────         ─────────       ──────────      │
│  HTTP/1.1+     HTTP/1.1+        HTTP/2          TCP/UDP         │
│  JSON/XML       JSON             Protobuf        Binary/Text     │
│  Resource       Graph            RPC             Full-duplex     │
│  based          based            based           streaming       │
│                                                                  │
│  CRUD           Flexible         High perf       Real-time      │
│  Universal      queries          internal        push/pull      │
└────────────────────────────────────────────────────────────────┘
```

---

## REST (Representational State Transfer)

REST maps operations onto HTTP verbs and URL resources:

```
Resource Model:
  GET    /users/123          → Fetch user 123
  POST   /users              → Create new user
  PUT    /users/123          → Replace user 123
  PATCH  /users/123          → Update fields of user 123
  DELETE /users/123          → Delete user 123

Nested resources:
  GET    /users/123/orders         → Orders for user 123
  POST   /users/123/orders         → Create order for user 123
  GET    /users/123/orders/456     → Specific order
```

### REST Strengths and Weaknesses

```
Strengths:
  ✓ Universal: every language, every framework has HTTP clients
  ✓ Cacheable: GET responses can be cached by CDN, browser
  ✓ Stateless: each request is self-contained
  ✓ Human-readable with JSON
  ✓ Familiar to every engineer

Weaknesses:
  ✗ Over-fetching: GET /users/123 returns all fields even if you need only name
  ✗ Under-fetching: loading a page may need 5-10 API calls (N+1 problem)
  ✗ No strong typing or schema enforcement (unless you add OpenAPI)
  ✗ HTTP/1.1 overhead (verbose headers, no multiplexing without HTTP/2)
```

### REST N+1 Problem

```
GET /timeline/posts         → returns [{post_id:1, user_id:10}, {post_id:2, user_id:11}, ...]
GET /users/10               → fetch author of post 1
GET /users/11               → fetch author of post 2
...
GET /users/110              → fetch author of post 100

= 101 HTTP requests to render 100 posts!
Solution: eager loading, response embedding, GraphQL, DataLoader pattern
```

---

## GraphQL

GraphQL lets clients specify exactly the data they need in a single request:

```
REST (over-fetching):
  GET /users/123
  Response: {
    id: 123, name: "Alice", email: "alice@...", phone: "...",
    address: {...}, preferences: {...}, billing: {...}, ...
  }
  Client needed: only name and avatar

GraphQL (exact data):
  POST /graphql
  Query:
    {
      user(id: 123) {
        name
        avatar
        posts(last: 5) {
          title
          createdAt
          likes
        }
      }
    }
  Response: exactly {name, avatar, posts[5]} — no waste

vs N+1 REST calls:
  1 GraphQL query = user + posts + avatars all in one round trip
```

### GraphQL Trade-offs

```
Strengths:
  ✓ Eliminates over/under-fetching
  ✓ Strongly typed schema (SDL)
  ✓ Introspective API (self-documenting)
  ✓ Single endpoint for all queries
  ✓ Client-driven: frontend teams can evolve without backend changes

Weaknesses:
  ✗ Complex to cache (POST requests, dynamic queries)
  ✗ N+1 problem shifts to resolvers (need DataLoader/batching)
  ✗ Complex authorization (field-level access control)
  ✗ Query complexity attacks (deeply nested queries can kill a server)
  ✗ Larger learning curve for teams new to it
```

### GraphQL vs REST: When to Use

| Choose REST | Choose GraphQL |
|-------------|----------------|
| Public API with diverse clients | Internal BFF (Backend for Frontend) |
| Heavy caching required | Complex data graphs (social network) |
| Simple CRUD resources | Mobile clients (minimize bandwidth) |
| External third-party integration | Frontend teams deploy independently |

---

## gRPC

gRPC uses Protocol Buffers (binary) over HTTP/2. It's designed for high-performance service-to-service communication:

```
Proto definition (contract-first):
  service UserService {
    rpc GetUser (GetUserRequest) returns (User);
    rpc ListUsers (ListUsersRequest) returns (stream User);
    rpc UpdateUser (UpdateUserRequest) returns (User);
    rpc Watch (WatchRequest) returns (stream Event);  ← bidirectional
  }

  message User {
    int64 id = 1;
    string name = 2;
    string email = 3;
  }

Auto-generated:
  - Client stub (Go, Java, Python, C++, Node.js, ...)
  - Server interface to implement
  - Serialization/deserialization code
```

### Protobuf vs JSON Size Comparison

```
JSON:
  {"id": 12345, "name": "Alice Smith", "email": "alice@example.com"}
  = 61 bytes

Protobuf:
  \x08\xb9`\x12\x0bAlice Smith\x1a\x11alice@example.com
  = ~35 bytes  (42% smaller)

For high-throughput services (100K RPS × 61 bytes = 6.1 MB/s vs 3.5 MB/s)
CPU saving: binary parse >> JSON text parse
```

### gRPC Streaming Modes

```
1. Unary RPC (like REST):
   Client ──── request ──────▶ Server
   Client ◀─── response ────── Server

2. Server streaming:
   Client ──── request ──────▶ Server
   Client ◀─── response 1 ─── Server
   Client ◀─── response 2 ─── Server
   Client ◀─── response 3 ─── Server  (e.g., live feed, file download)

3. Client streaming:
   Client ──── data 1 ───────▶ Server
   Client ──── data 2 ───────▶ Server  (e.g., file upload, telemetry)
   Client ◀─── response ────── Server

4. Bidirectional streaming:
   Client ◀──── data ──────── Server
   Client ──── data ──────▶ Server
   (e.g., chat, collaborative editing, game state sync)
```

### gRPC Trade-offs

```
Strengths:
  ✓ 2-5× faster than JSON/REST (binary, HTTP/2, multiplexing)
  ✓ Strongly typed, auto-generated clients
  ✓ Bidirectional streaming
  ✓ Built-in load balancing, retries, timeouts (gRPC interceptors)
  ✓ Excellent for polyglot microservices

Weaknesses:
  ✗ Not human-readable (binary wire format)
  ✗ Poor browser support (requires gRPC-Web proxy)
  ✗ Schema evolution requires careful field versioning
  ✗ Debugging harder (need grpcurl, not just curl)
  ✗ Requires HTTP/2 (more complex infrastructure)
```

---

## Choosing the Right Paradigm

```
Decision Tree:

Is this a public/external API?
  Yes → REST (or GraphQL for mobile/flexible queries)
  No → gRPC for internal service-to-service

Does the client need real-time bidirectional data?
  Yes → WebSocket (or gRPC bidirectional streaming)
  No → Continue

Is the client frontend with complex data needs?
  Yes → GraphQL (BFF pattern)
  No → REST

Is raw throughput critical (1M+ RPS)?
  Yes → gRPC
  No → REST is fine
```

---

## API Paradigm Comparison Table

| | REST | GraphQL | gRPC | WebSocket |
|---|------|---------|------|-----------|
| Transport | HTTP | HTTP | HTTP/2 | TCP/UDP |
| Format | JSON | JSON | Protobuf | Any |
| Schema | Optional (OpenAPI) | SDL (required) | .proto (required) | None |
| Caching | Excellent | Hard | HTTP/2 push only | N/A |
| Browser support | Native | Native | gRPC-Web only | Native |
| Streaming | No (SSE workaround) | Subscriptions | Yes (4 modes) | Yes |
| Type safety | Weak | Strong | Strong | None |
| Learning curve | Low | Medium | High | Low |
| Best for | Public APIs | Mobile, complex UI | Internal microservices | Real-time |

---

## Interview Quick Answers

- **Why use gRPC over REST for internal services?** — Binary protocol, HTTP/2 multiplexing, auto-generated clients, 2-5× lower overhead, bidirectional streaming.
- **What is the N+1 problem in REST?** — Fetching a list of N items then making N more requests for related data. Fix: batch endpoints, GraphQL, eager loading.
- **When would you choose GraphQL?** — Mobile clients (bandwidth-sensitive), BFF pattern, when frontend teams need flexibility without backend changes.
- **Can gRPC be used from a browser?** — Not directly. Requires gRPC-Web (an HTTP/1.1-compatible proxy). Alternatively, use Connect-Go (supports both gRPC and REST from browser).
