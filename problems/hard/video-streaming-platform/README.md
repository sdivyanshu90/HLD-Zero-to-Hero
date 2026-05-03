# Video Streaming Platform — System Design Walkthrough

**Difficulty:** Hard  
**Tags:** HLS, adaptive bitrate, CDN, transcoding, chunked upload  
**Companies:** Netflix, YouTube, Twitch, Vimeo

---

## Problem Statement

Design a video streaming platform (like YouTube) that:
- Handles 5 M video uploads/day (avg 50 MB each)
- Streams to 1 B users/day with adaptive bitrate
- Processes and transcodes videos within 5 minutes of upload
- Serves 90% of traffic through CDN to minimize origin load

---

## Architecture Diagram

```
Video Upload
    │
    ▼
┌─────────────────────┐
│  Upload Service     │  chunked upload (TUS protocol)
│  (multi-part S3)    │
└─────────┬───────────┘
          │ trigger
          ▼
┌─────────────────────────────────────┐
│  Transcoding Pipeline               │
│  Kafka → GPU Workers → S3 (HLS)    │
│  360p, 480p, 720p, 1080p, 4K       │
└─────────┬───────────────────────────┘
          │
          ▼
┌─────────────────────┐
│  CDN (CloudFront /  │  caches .m3u8 manifests + .ts segments
│  Fastly)            │
└─────────┬───────────┘
          │
          ▼
     Client Player (HLS.js)
     Adaptive Bitrate Selection
```

---

## Study Order

1. [Requirements](01-requirements.md)
2. [Traffic and Bandwidth Shape](02-traffic-and-bandwidth-shape.md)
3. [Upload and Transcoding Pipeline](03-upload-and-transcoding-pipeline.md)
4. [Storage and Origin Serving](04-storage-and-origin-serving.md)
5. [CDN and Origin Offload](05-cdn-and-origin-offload.md)
6. [Adaptive Bitrate Playback](06-adaptive-bitrate-playback.md)
7. [Watch History and Analytics](07-watch-history-and-analytics.md)
8. [Checkpoint](08-checkpoint.md)
