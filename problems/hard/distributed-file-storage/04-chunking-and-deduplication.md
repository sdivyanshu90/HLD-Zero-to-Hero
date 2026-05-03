# Step 4 — Chunking and Deduplication

## Why Chunk Files?

```
Problem: Upload 5 GB file, network drops at 4.9 GB
Solution: Split into 4 MB chunks, track per-chunk upload status

Benefits:
  1. Resume from last chunk (not from scratch)
  2. Parallel upload of chunks (multiple connections)
  3. Delta sync: only upload changed chunks on file edit
  4. Cross-user deduplication: if chunk exists, skip upload
```

## Fixed vs Variable Chunking

```
Fixed-size chunking (4 MB):
  Simple, predictable
  Problem: edit at start shifts ALL chunk boundaries
  Edit "Hello World" → "Hello Beautiful World"
    All downstream chunk hashes change → must re-upload everything

Variable-size chunking (Rabin fingerprinting / rolling hash):
  Find chunk boundaries based on content, not position
  Edit in middle: only the modified chunk changes; rest unchanged
  Dropbox uses: 4 MB average chunks with Rabin fingerprint CDC
  Range: 0.5 MB min, 16 MB max
```

## Content-Addressable Storage

```
Each chunk is stored by its SHA-256 hash:
  chunk_hash = SHA256(chunk_data)
  S3 key     = "chunks/{chunk_hash}"

Upload flow:
  1. Client computes SHA256 for each chunk
  2. Client asks server: "Do you have these hashes?"
     POST /api/chunks/check  body: ["abc123...", "def456..."]
     Response: {"missing": ["abc123..."]}
  3. Client uploads ONLY missing chunks
  4. Identical chunks shared across ALL users (dedup!)

Deduplication savings:
  If user A and B both have the same 4K photo:
    Only 1 copy stored in S3
    Metadata table records both users own that chunk_hash
```

## Deduplication Metadata Schema

```sql
-- File metadata
CREATE TABLE files (
    file_id     UUID PRIMARY KEY,
    user_id     BIGINT,
    path        TEXT,
    size        BIGINT,
    version     INT,
    created_at  TIMESTAMPTZ,
    modified_at TIMESTAMPTZ
);

-- File → chunks mapping
CREATE TABLE file_chunks (
    file_id     UUID,
    chunk_seq   INT,        -- position in file
    chunk_hash  CHAR(64),   -- SHA-256 hex
    chunk_size  INT,
    PRIMARY KEY (file_id, chunk_seq)
);

-- Chunk data (pointer to S3)
CREATE TABLE chunks (
    chunk_hash  CHAR(64) PRIMARY KEY,
    s3_key      TEXT,
    size        INT,
    ref_count   INT,        -- how many files reference this chunk
    created_at  TIMESTAMPTZ
);
```

## Dedup Ratio

```
Typical dedup ratios:
  Photos:     2-5×   (many duplicate photos shared via social)
  Documents:  1.5-3× (many users have same PDFs, templates)
  Videos:     1.1-1.5× (large files, less sharing)
  Overall:    ~2× deduplication ratio

25 PB logical storage → ~12-15 PB physical after dedup
Savings: ~10 PB × $0.023/GB = ~$230M/year in S3 costs!
```
