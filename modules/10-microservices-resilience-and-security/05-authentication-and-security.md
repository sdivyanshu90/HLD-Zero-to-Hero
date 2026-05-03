# Authentication, Authorization, and Transport Security

## Authentication vs Authorization

```
Authentication: WHO are you? → verify identity → issue token
Authorization:  WHAT can you do? → check permissions → allow/deny

AuthN flow (login):
  1. User provides credentials (username/password)
  2. Server verifies against stored hash (bcrypt, argon2)
  3. Server issues JWT token (or session cookie)
  4. Subsequent requests include JWT → server validates

AuthZ check (resource access):
  1. Verify JWT is valid (signature, expiry)
  2. Extract claims: {user_id: 123, role: "admin", scope: ["read:orders", "write:orders"]}
  3. Check: does user's role/scope allow this action?
  4. Allow or deny with 403 Forbidden
```

---

## JWT: JSON Web Tokens

```
JWT structure: header.payload.signature

Header (base64):  {"alg": "RS256", "typ": "JWT"}
Payload (base64): {
  "sub": "user_123",          ← subject (user ID)
  "iss": "auth.example.com",  ← issuer
  "aud": "api.example.com",   ← audience
  "exp": 1703123456,          ← expiry (Unix timestamp)
  "iat": 1703119856,          ← issued at
  "scope": "read:orders write:orders",
  "role": "customer"
}
Signature: RS256(header + "." + payload, private_key)

Verification (by any service):
  1. Decode header and payload (base64, not encrypted)
  2. Verify signature using PUBLIC key (no need to call auth service!)
  3. Check exp > now (not expired)
  4. Check iss and aud (expected issuer and audience)

Key insight: JWT is STATELESS
  No database lookup needed to validate (just cryptographic verification)
  Any service with the public key can independently verify
  Trade-off: cannot revoke before expiry (unless token blacklist)

Token expiry strategy:
  Access token: short lived (15 min to 1 hour)
    → If stolen, attacker has limited time window
    → Cannot revoke individual tokens without blacklist
  Refresh token: long lived (7-30 days), stored securely
    → Used to get new access tokens without re-login
    → Can be revoked in DB (logout, account compromise)

JWT security rules:
  ✓ ALWAYS verify signature (never trust claims without verification)
  ✓ Use asymmetric keys (RS256, ES256) not symmetric (HS256) for microservices
     HS256: shared secret → every service that validates must know secret
     RS256: private key signs (auth service only), public key verifies (any service)
  ✓ Set short expiry (15-60 min)
  ✓ Validate aud (intended audience) to prevent token replay across services
  ✗ NEVER store sensitive data in JWT payload (it's base64, not encrypted!)
```

---

## OAuth 2.0 and OIDC

```
OAuth 2.0: authorization framework (third-party access delegation)
  Use case: "Allow GitHub to access your Google Contacts"
  
  Roles:
    Resource Owner: user (controls their data)
    Client: application requesting access (GitHub)
    Authorization Server: issues tokens (Google's auth server)
    Resource Server: API that holds the data (Google Contacts API)
  
  Authorization Code Flow (most secure, for server-side apps):
    1. Client redirects user to Auth Server
       GET /authorize?client_id=github&scope=contacts&response_type=code&redirect_uri=...
    2. User authenticates and consents
    3. Auth Server redirects back with authorization code
    4. Client exchanges code for access token (server-to-server, code can only be used once)
    5. Client uses access token to call Resource Server

OpenID Connect (OIDC): OAuth 2.0 + identity layer
  Adds "who is this user?" on top of "what can this app do?"
  Returns: access token (for APIs) + ID token (JWT with user profile)
  Standard claims: sub, email, name, picture, locale
  
  Used by: "Login with Google", "Login with GitHub"
  
PKCE (Proof Key for Code Exchange):
  For public clients (mobile apps, SPAs) that can't keep a secret
  Client generates code_verifier, sends code_challenge = SHA256(code_verifier)
  On token exchange: client proves it has the code_verifier
  Prevents authorization code interception attacks
```

---

## mTLS: Mutual TLS for Service-to-Service

```
Regular TLS: client verifies server identity
  Client → [validate server cert] → Server
  Server doesn't know who the client is!
  
  Used for: browser → web server (any browser can connect)

mTLS (Mutual TLS): both parties verify each other
  Client presents cert → Server verifies client cert
  Server presents cert → Client verifies server cert
  Both authenticated, channel encrypted
  
  Used for: service-to-service in microservices (zero-trust networking)
  "payment-service" cert proves it's really payment-service
  "order-service" won't talk to anything that doesn't have a valid cert

Certificate management in k8s:
  cert-manager: automatically provisions and rotates certs (Let's Encrypt, Vault)
  Service mesh (Istio): automatically manages mTLS between all services
    SPIFFE/SPIRE: workload identity standard
    Each pod gets a cert: spiffe://cluster.local/ns/default/sa/payment-service

mTLS without service mesh (manual):
  Each service needs:
    - CA root cert (to verify peer certs)
    - Its own cert + private key
    - TLS configuration in code
  → Very complex at scale → service mesh is the practical solution
```

---

## Security Checklist for System Design

```
At the API boundary:
  ✓ HTTPS/TLS everywhere (no plaintext HTTP in production)
  ✓ JWT validation: signature, expiry, audience, issuer
  ✓ Rate limiting (prevents brute force, DDoS)
  ✓ Input validation: reject unexpected input types/sizes
  ✓ OWASP Top 10: SQL injection (parameterized queries), XSS (output encoding)

At the service layer:
  ✓ mTLS for service-to-service
  ✓ Principle of least privilege: services only have DB permissions they need
  ✓ Secrets in secret manager (AWS Secrets Manager, Vault), not hardcoded
  ✓ Audit logging: who did what, when, to which resource

At the data layer:
  ✓ Encryption at rest (AES-256) for sensitive data
  ✓ Separate encryption keys per tenant (multi-tenant systems)
  ✓ PII tokenization: store hash/token, not raw PII in most tables
  ✓ DB access through service accounts, not shared credentials
```

---

## Interview Quick Answers

- **Why use RS256 instead of HS256 for JWT?** — HS256 uses a shared secret for both signing and verification. Every service that validates JWTs must know the secret, creating multiple secret holders (security risk). RS256 uses asymmetric keys: only the auth service has the private key (signing), all services have the public key (verification only). Compromise of one service doesn't expose the signing key.
- **What is the difference between authentication and authorization?** — Authentication: verifying identity (who are you? → JWT validates identity). Authorization: verifying permissions (what can you do? → checking role/scope/ACLs). Most security frameworks separate these: auth middleware validates JWT (AuthN), then authorization middleware checks permissions (AuthZ).
- **What is mTLS and when do you use it?** — Mutual TLS: both client and server present certificates for authentication. Used for zero-trust service-to-service communication in microservices. Prevents a compromised internal service from impersonating another service. Typically managed by a service mesh (Istio) to avoid per-service certificate management.
