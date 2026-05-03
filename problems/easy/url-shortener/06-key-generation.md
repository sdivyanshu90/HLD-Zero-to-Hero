# Step 6 — Key Generation

## Option A: Random Generation + Collision Check

```python
import secrets, string

ALPHABET = string.ascii_letters + string.digits  # 62 chars

def generate_code(length=7) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

def create_short_url(long_url: str, db, bloom_filter) -> str:
    for _ in range(10):  # max 10 attempts
        code = generate_code()
        if not bloom_filter.contains(code):  # fast negative check
            try:
                db.insert(code, long_url)    # will raise on collision
                bloom_filter.add(code)
                return code
            except UniqueConstraintError:
                continue  # rare: race condition
    raise Exception("Could not generate unique code")
```

**Collision probability with 6 B codes in 3.5 T space:**
```
P(collision) = 6 B / 3.5 T ≈ 0.17 %  per attempt
After 10 attempts: (0.0017)^10 ≈ negligible
```

## Option B: Pre-Generated Key Table (KGS — Key Generation Service)

```
Offline batch job:
  1. Generate 100 M random 7-char codes
  2. INSERT INTO available_codes (code, used=false)
  3. Run daily to refill

On write request:
  BEGIN;
  SELECT code FROM available_codes WHERE used=false LIMIT 1 FOR UPDATE;
  UPDATE available_codes SET used=true WHERE code = ?;
  INSERT INTO short_urls (short_code, long_url, ...);
  COMMIT;
```

**Advantages:**
- Zero collision risk at insert time
- No bloom filter needed
- Codes are already validated unique

**Disadvantages:**
- Extra table and batch job
- Lock contention on `available_codes` at high write rates (mitigate: assign ranges per server)

## Option C: Counter-Based (MD5/SHA truncation)

```
code = base62(sha256(long_url + salt))[:7]
```

**Problem:** Same URL always produces same code (deterministic — can be a feature or bug).  
**Collision risk:** Two different URLs may produce same 7-char prefix (birthday paradox).

## Recommendation

| Scale | Approach |
|-------|----------|
| < 10K writes/sec | Random + bloom filter (Option A) |
| > 10K writes/sec | Pre-generated KGS pool (Option B) |
| Deterministic desired | Hash-based (Option C) with collision retry |

## Bloom Filter Sizing

```
n = 6 B entries, p = 0.001 (0.1% false positive rate)
m = -n × ln(p) / (ln(2))^2 = 8.6 B bits ≈ 1.1 GB RAM
k = (m/n) × ln(2) = 10 hash functions
→ Fits in a single Redis instance
```
