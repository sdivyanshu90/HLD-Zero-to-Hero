# Step 3 — API Design

## REST Endpoints

### Create Short URL

```
POST /api/v1/urls
Content-Type: application/json

{
  "long_url": "https://example.com/very/long/path?with=params",
  "custom_alias": "my-link",   // optional
  "ttl_days": 365              // optional, null = never expire
}
```

**Response 201 Created**
```json
{
  "short_url": "https://short.ly/aB3xK9z",
  "short_code": "aB3xK9z",
  "long_url": "https://example.com/very/long/path?with=params",
  "expires_at": "2027-05-01T00:00:00Z"
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| 400 | Invalid URL or alias format |
| 409 | Custom alias already taken |
| 429 | Rate limit exceeded |

---

### Redirect

```
GET /{short_code}
```

**Response (success):**
```
HTTP/1.1 301 Moved Permanently      ← 301 for SEO / caching
Location: https://example.com/...
Cache-Control: max-age=86400
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 404 | Short code not found |
| 410 | Short code expired / deleted |

---

### Delete (optional v2)

```
DELETE /api/v1/urls/{short_code}
Authorization: Bearer <token>
```

---

## Rate Limiting Strategy

```
Token bucket per IP:
  burst = 10 requests
  refill = 1 request / second

Apply at API Gateway (e.g. nginx + lua, or Kong)
Return Retry-After header on 429
```

## Idempotency

Submitting the same `long_url` twice within 24 h returns the existing short code (dedup via DB unique index on `long_url`).
