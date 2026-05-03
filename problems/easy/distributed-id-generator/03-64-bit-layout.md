# Step 3 — 64-Bit Layout

## Bit Field Diagram

```
Bit 63 (MSB)                                              Bit 0 (LSB)
┌──────┬──────────────────────────────────────┬──────────────┬──────────────┐
│  0   │          timestamp (41 bits)          │  worker (10b) │  seq (12b)  │
└──────┴──────────────────────────────────────┴──────────────┴──────────────┘
  sign           ms since custom epoch          0-1023          0-4095
```

## Example ID Calculation

```python
EPOCH   = 1577836800000  # 2020-01-01 00:00:00 UTC in ms
ts      = 1714694400000  # 2024-05-03 00:00:00 UTC in ms
worker  = 42
seq     = 7

id = ((ts - EPOCH) << 22) | (worker << 12) | seq
   = (136_857_600_000 << 22) | (42 << 12) | 7
   = 574_903_418_552_320 + 172032 + 7
   = 574_903_418_724_359
```

## Decoding an ID

```python
def decode(snowflake_id: int):
    seq      = snowflake_id & 0xFFF          # bits 0-11
    worker   = (snowflake_id >> 12) & 0x3FF  # bits 12-21
    ts_ms    = (snowflake_id >> 22) + EPOCH  # bits 22-62
    return ts_ms, worker, seq
```

## Alternative Layouts

| Layout | Use Case |
|--------|----------|
| Standard Snowflake (41+10+12) | General purpose |
| Discord (42+10+12) | Extends time to 139 years |
| Instagram (41+13+10) | More shards (8192), fewer seq (1024/ms) |
| MongoDB ObjectId (32+5+3+24 bits) | 96-bit, includes process ID |
| ULIDv1 (48ms + 80 random) | 128-bit, URL-safe base32 |

## Sorting Property

```
ID A generated at t=100: 100 << 22 = 419430400
ID B generated at t=200: 200 << 22 = 838860800

A < B  ✓  (time-sortable)

Same ms, different seq:
ID A: seq=0 → (100 << 22) | 0 = 419430400
ID B: seq=1 → (100 << 22) | 1 = 419430401
A < B  ✓  (monotonic within ms)
```
