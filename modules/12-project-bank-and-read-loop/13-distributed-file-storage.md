# Cheat Sheet: Distributed File Storage

## Scale (BoE)
```
Files stored: 1B files
Average file size: 1 MB (mixed: docs 50KB, images 5MB, videos 500MB)
Total storage: 1B × 1 MB = 1 PB (minimum)
Daily uploads: 10M new files/day → 10 TB/day ingest
Download QPS: 100M downloads/day → 1,200 download RPS
```

## System Diagram
```
Client ──upload──▶ API Server ──▶ Metadata DB (file_id, name, path, chunks)
                       │
                  Chunk Split (4 MB chunks)
                       │
                  ┌────┼────┐
                  ▼    ▼    ▼
               Chunk Storage Nodes (consistent hashing)
               (3 replicas per chunk, rack-aware placement)

Client ──download──▶ API Server ──▶ Metadata DB (lookup chunk list)
                                         │
                                   Fetch chunks from storage nodes
                                         │
                                   Stream to client
```

## Chunking Strategy

```
Large file split into 4 MB chunks:
  file.mkv (400 MB) → 100 chunks of 4 MB each
  
  Each chunk: content-addressed (SHA-256 hash of content = chunk ID)
  Same content → same chunk ID → DEDUPLICATION!
  
  If two users upload same file: store only ONE copy of each chunk
  Metadata DB: user A → [chunk1, chunk2, ...], user B → [chunk1, chunk2, ...]
  Both point to same physical chunks!
  
  Metadata per file:
    file_id, user_id, name, size, created_at
    chunks: [chunk_id_1, chunk_id_2, ..., chunk_id_100] (ordered list)
  
  Metadata per chunk:
    chunk_id (SHA-256 hash), size, storage_nodes [node1, node2, node3]
```

## Replication Strategy

```
Each chunk replicated 3×, rack-aware:
  Node 1 (rack A, AZ 1)
  Node 2 (rack B, AZ 1)
  Node 3 (rack C, AZ 2)
  
  Can survive: 2 node failures, 1 AZ failure without data loss
  
  Chunk placement via consistent hashing:
    hash(chunk_id) → primary node on ring
    Next 2 nodes on ring → replicas (skip same rack)
    
  On node failure:
    Detect via heartbeat (no heartbeat in 30s → node dead)
    Re-replicate affected chunks to new nodes from remaining replicas
    Repair in background, don't block reads
```

## Bottlenecks
1. Metadata DB: 1B files × ~10 chunks each = 10B chunk records → shard by user_id
2. Hot chunks: popular files downloaded concurrently → CDN for read-heavy files, content-addressed so cacheable forever (chunk_id = hash of content, immutable)

## Unique Trick
Content-addressable storage: chunk ID = SHA-256 of chunk content. This enables: (1) automatic deduplication (same content = same ID = stored once), (2) built-in integrity verification (download chunk → recompute hash → must match), (3) CDN-friendly caching (chunk ID never changes for same content).
