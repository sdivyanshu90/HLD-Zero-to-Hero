# Cheat Sheet: Video Streaming Platform

## Scale (BoE)
```
Total videos: 800M (YouTube scale)
Daily video uploads: 500 hours of video per minute → 720K hours/day
Daily video views: 1B views/day → 11,600 view starts/second
Concurrent streams: 5M (each using 5 Mbps for 1080p)
Total streaming bandwidth: 5M × 5 Mbps = 25 Tbps → CDN critical!
Storage: 500 hours/min × 1 GB/min = 500 GB/min = 720 TB/day uploads
```

## Upload and Transcoding Pipeline

```
Creator uploads video ──▶ API Server ──▶ S3 (raw upload)
                                              │
                                         Message Queue (Kafka)
                                              │
                                    Transcoding Workers (GPU)
                                         │         │
                              ┌──────────┤         ├──────────┐
                              ▼          ▼         ▼          ▼
                           4K        1080p       720p       480p
                          (2 GB)    (500 MB)   (200 MB)   (100 MB)
                              │
                           Upload each quality to CDN origin
                           Update video metadata DB (status: READY)
                           Notify creator (webhook/email)
```

## Adaptive Bitrate Streaming (ABR)

```
MPEG-DASH and HLS:
  Video split into 4-10 second segments (chunks)
  Each segment available in multiple qualities
  
  Manifest file (m3u8 or MPD):
    #EXT-X-STREAM-INF:BANDWIDTH=8000000  → 1080p
    video_1080p.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=3000000  → 720p
    video_720p.m3u8
  
  Player downloads manifest → picks quality based on network bandwidth
  Measures download speed every segment → switches quality up/down
  Buffer: player pre-buffers 10-30 seconds ahead (smooth playback)
```

## System Diagram
```
Client ──request manifest──▶ CDN Edge (PoP)
           │ (miss)
           └──▶ CDN Origin (video segments stored here)
                      │
                      └──▶ S3 (long-term storage, cost-efficient)

View count tracking:
  Client ──view event──▶ Kafka ──▶ Stream Processor ──▶ Cassandra (view counts)
  (async, non-blocking)
```

## Key Design Decisions

**1. CDN placement:**
- 25 Tbps bandwidth → impossible from origin → MUST use CDN
- CDN caches popular videos at PoPs globally
- Long-tail videos (rarely watched): fetched from origin, not cached at edge

**2. Storage tiering:**
- Hot (recent/popular): CDN edge → fast, expensive
- Warm: CDN origin → medium cost
- Cold (2+ years old, rarely watched): S3 Glacier → very cheap

**3. Comment system:**
- Fanout: video with 10M viewers → comment section needs to handle high read throughput
- Pagination + Redis cache for top comments

## Unique Trick
Chunked upload with resumable uploads (TUS protocol): client uploads video in 4 MB chunks. If network drops, resume from last successful chunk. S3 multipart upload supports this natively.
