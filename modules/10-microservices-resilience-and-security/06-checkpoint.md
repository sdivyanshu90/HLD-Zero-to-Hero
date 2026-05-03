# Module 10 Checkpoint: Microservices, Resilience and Security

## Questions

---

**Q1.** Your checkout service calls 4 downstream services (Inventory, Payment, Shipping, Email). What patterns would you apply to ensure resilience?

> **Answer:**
> 1. **Timeouts** on every downstream call (e.g., Inventory=500ms, Payment=2s, Shipping=1s, Email=500ms)
> 2. **Circuit Breakers**: if Inventory fails >50% of requests → open circuit → return error immediately (no waiting for timeouts)
> 3. **Bulkheads**: separate thread pools for each downstream service. Slow Email service won't fill threads needed for Inventory/Payment
> 4. **Retries with backoff**: retry idempotent operations (GET inventory check) with exponential backoff. NOT for POST (charge payment) unless idempotency keys are used
> 5. **Fallbacks**: if Shipping ETA unavailable → show "3-5 days" instead of failing the whole checkout
> 6. **Saga pattern**: for distributed transaction across Inventory + Payment → use compensating transactions on failure

---

**Q2.** How do you implement exactly-one-charge semantics for payment processing?

> **Answer:**
> 1. Client generates a **unique idempotency key** (UUID) per payment attempt, sends it in header: `Idempotency-Key: uuid-xxx`
> 2. Payment Service: before charging, check DB: `SELECT * FROM idempotency_keys WHERE key = 'uuid-xxx'`
>    - If found: return cached result (no charge)
>    - If not found: proceed with charge
> 3. After charging: store in idempotency_keys table (key, result, expires_at) atomically in same transaction
> 4. On retry (network timeout): client sends same idempotency key → server returns cached result → no double charge
> 5. Expire idempotency records after 24-48 hours (clients retry window)

---

**Q3.** Why should JWT access tokens have a short expiry (15 min)?

> **Answer:** JWTs are stateless — once issued, they cannot be revoked before expiry (without a token blacklist). If a token is stolen, the attacker has access until the token expires. A 15-minute window limits the blast radius. After expiry, the client must use the refresh token to obtain a new access token. The refresh token is long-lived but can be stored server-side and explicitly revoked (on logout, account compromise). This gives: fast stateless validation (no DB lookup for access token) + revocability (refresh token in DB can be deleted).

---

**Q4.** You have 200 microservices and need to add mTLS between all of them. How?

> **Answer:** Implement a service mesh (Istio + Envoy):
> 1. Deploy Istio control plane to k8s cluster
> 2. Enable automatic sidecar injection (annotation on namespace)
> 3. Istio automatically injects Envoy sidecar into each pod
> 4. Envoy handles mTLS transparently (app code unchanged)
> 5. Istio issues SPIFFE-compliant certs to each workload (via cert-manager + Istio CA)
> 6. Certs auto-rotated every 24 hours
> 7. Apply PeerAuthentication policy: STRICT (reject non-mTLS connections)
> Net: 200 services get mTLS with zero code changes, automatic cert management.

---

**Q5.** Your API is getting 10,000 requests/second from a single IP. How do you rate limit?

> **Answer:**
> 1. **Algorithm**: Token bucket or sliding window counter (Cloudflare uses sliding window)
> 2. **Storage**: Redis `INCR rate:{ip}:{window}` atomic counter per minute window
> 3. **Response**: return HTTP 429 Too Many Requests with `Retry-After: 60` header
> 4. **Tiers**: per-IP limit (prevents abuse) + per-user limit (authenticated) + global limit (protect infrastructure)
> 5. **Rate limit headers**: `X-RateLimit-Limit: 1000`, `X-RateLimit-Remaining: 750`, `X-RateLimit-Reset: 1703120000`
> 6. **DDoS**: for large-scale attacks, move rate limiting to CDN/WAF layer (Cloudflare, AWS Shield) before traffic reaches your servers

---

## Checklist

- [ ] Monolith vs microservices: trade-offs, when to use each, Conway's Law
- [ ] API Gateway: routing, auth, rate limiting, SSL termination, BFF pattern
- [ ] Circuit breaker: CLOSED/OPEN/HALF-OPEN states, failure threshold, auto-recovery
- [ ] Bulkhead: thread pool isolation per dependency
- [ ] Timeout: connect + read timeout, aggressive timeouts + circuit breaker
- [ ] Rate limiting: token bucket (burst-friendly), leaky bucket (smooth), sliding window counter (hybrid)
- [ ] Service discovery: client-side (Eureka) vs server-side (Consul+LB)
- [ ] Service mesh: sidecar proxy, mTLS, retries, circuit breakers as config not code
- [ ] JWT: header.payload.signature, RS256 vs HS256, short access token + long refresh token
- [ ] OAuth2/OIDC: authorization code flow, PKCE for public clients
- [ ] mTLS: mutual cert verification, service mesh manages at scale
- [ ] Security checklist: TLS everywhere, secrets in vault, least privilege, audit logs
