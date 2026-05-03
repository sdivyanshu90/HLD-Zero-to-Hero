# Step 8 — Checkpoint & Interview Q&A

**Q1: Why use content-addressable storage (hash as key)?**
> SHA-256(chunk_data) as the storage key automatically deduplicates identical chunks across all users. If two users upload the same 4 MB chunk, only one copy is stored. Verification is free (recompute hash and compare). No need for a separate dedup index beyond the chunks table.

**Q2: How do you handle concurrent edits to the same file from two devices?**
> Last-write-wins with conflict copy: when device B uploads a new version but the server's current version was modified by device A after B's last sync, the server creates a conflict copy (e.g., "report (Device B's conflicted copy 2024-05-03).docx"). Both versions are preserved. User resolves manually. Google Docs avoids this with CRDT/OT at the character level.

**Q3: How does delta sync work?**
> Client maintains a local index of (file_path → [chunk_hashes]). On file change, recompute chunk hashes (using rolling hash for variable-size chunks). Compare new hashes to local index — only changed chunks have new hashes. Upload only those chunks. Update metadata with new file version. On large file with small edit, often only 1-2 chunks change.

**Q4: How do you serve downloads efficiently?**
> For small files (< 1 MB): reassemble from chunks in memory, return directly. For large files: server generates a temporary signed S3 URL for each chunk, returns ordered list of signed URLs to client. Client downloads chunks in parallel (e.g., 4 concurrent connections) and assembles locally. No data flows through API server.

**Q5: How do you replicate 25 PB reliably?**
> S3 standard storage: 3× replication across 3 availability zones automatically. For cross-region durability (e.g., US + EU): S3 cross-region replication rule. For critical data: additional Glacier copy for backup. RTO/RPO: < 1 hour for region failure with CRR enabled.
