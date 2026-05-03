# Step 8 — Checkpoint & Interview Q&A

**Q1: Why use HLS instead of a single MP4 file for streaming?**
> HLS (HTTP Live Streaming) segments video into 6-second .ts chunks. This enables: (1) Adaptive bitrate — switch quality at any segment boundary. (2) Seek anywhere — jump to any timestamp by fetching that segment. (3) CDN-friendly — tiny files that CDN caches efficiently. (4) Parallel download — prefetch next segments while current plays.

**Q2: How does adaptive bitrate work?**
> The HLS master manifest lists multiple bitrate variants (360p, 480p, 720p, 1080p). The player monitors download speed and buffer level every segment. If download speed drops below the next segment's bitrate, the player switches to a lower quality variant. Target: keep buffer ≥ 30 seconds ahead. Switch up when buffer > 45 seconds and speed supports it.

**Q3: How do you handle a video that goes viral (sudden 10× traffic spike)?**
> CDN absorbs the spike — each PoP caches the manifest and segments independently. Origin S3 sees at most 1 request per segment per CDN PoP (typically 1 miss, then cached). For truly viral content, pre-warm CDN edges by fetching the manifest and first 10 segments in all PoPs as soon as the video gets N views per minute.

**Q4: How do you prevent users from downloading your premium content?**
> (1) Signed URLs: S3/CDN generates time-limited, user-specific URLs for each .ts segment (valid for 1 hour). Even if URL is shared, it expires. (2) DRM: Widevine (Chrome/Android), FairPlay (Safari/iOS), PlayReady (Edge) encrypt video keys, require licensed player. (3) Watermarking: embed invisible user ID in video — trace piracy source.

**Q5: What is the storage cost for 5 M uploads/day at scale?**
> 5 M uploads × 50 MB raw = 250 TB/day raw. After transcoding to 5 resolutions at ~60% compression: 5 M × 50 MB × 5 × 0.6 = 750 TB/day. S3 cost: ~$0.023/GB/month. 750 TB = $17,250/day for hot storage. In practice: lifecycle policies move to S3 IA (< 90d) and Glacier (> 1 year), reducing cost to $2-5K/day.
