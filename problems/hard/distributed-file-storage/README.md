# Distributed File Storage — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** chunking, deduplication, content-addressable, replication, sync  
**Companies:** Dropbox, Google Drive, Box, OneDrive

---

## Problem Statement

Design a cloud file storage and sync system (like Dropbox) that:
- Stores and syncs files across multiple devices
- Handles 500 M users with 50 GB each = 25 PB total
- Supports concurrent edits and conflict detection
- Deduplicates identical file chunks across all users

---

## Architecture Diagram

```
Client (Desktop / Mobile)
    │  Delta sync (only changed chunks)
    │
    ▼
┌─────────────────────────┐
│  API Gateway + Auth     │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌──────────┐  ┌──────────────────┐
│ Metadata │  │  Block Service   │  stores chunks
│ Service  │  │  (content-addr.) │
│(Postgres)│  └────────┬─────────┘
└──────────┘           │
                       ▼
                ┌────────────────┐
                │  S3 / HDFS     │  content-addressable storage
                │  key=SHA256    │  of chunk data
                └────────────────┘
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Storage and Metadata Split](02-storage-and-metadata-split.md)
3. [Upload and Sync Flow](03-upload-and-sync-flow.md)
4. [Chunking and Deduplication](04-chunking-and-deduplication.md)
5. [Versioning and Conflict Handling](05-versioning-and-conflict-handling.md)
6. [Sharing and Download Serving](06-sharing-and-download-serving.md)
7. [Failure Modes and Recovery](07-failure-modes-and-recovery.md)
8. [Checkpoint](08-checkpoint.md)
