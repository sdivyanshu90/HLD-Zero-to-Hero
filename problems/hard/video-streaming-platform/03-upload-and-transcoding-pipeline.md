# Step 3 — Upload and Transcoding Pipeline

## Chunked Upload (TUS Protocol)

```
Problem: 50 MB video upload; network drops at 45 MB
Solution: Resume from last good chunk

TUS Protocol:
  POST   /upload           → create upload session, get upload_id
  PATCH  /upload/{id}      → upload chunk (offset-based)
  HEAD   /upload/{id}      → query current offset (for resume)
  DELETE /upload/{id}      → cancel upload

Client:
  chunk_size = 5 MB
  for chunk in chunks:
    PATCH /upload/{id} with Content-Range: bytes 0-4999999
    retry up to 3× on network error
    resume from HEAD-returned offset on failure
```

## S3 Multipart Upload

```python
import boto3
s3 = boto3.client('s3')

# Initiate
mpu = s3.create_multipart_upload(Bucket='raw-videos', Key=video_id)

# Upload parts (can be parallel)
parts = []
for i, chunk in enumerate(read_chunks(file, chunk_size=5*1024*1024)):
    resp = s3.upload_part(
        Bucket='raw-videos', Key=video_id,
        PartNumber=i+1, UploadId=mpu['UploadId'],
        Body=chunk
    )
    parts.append({'PartNumber': i+1, 'ETag': resp['ETag']})

# Complete
s3.complete_multipart_upload(
    Bucket='raw-videos', Key=video_id,
    UploadId=mpu['UploadId'],
    MultipartUpload={'Parts': parts}
)
```

## Transcoding Pipeline

```
S3 upload triggers Lambda/SNS event
  → publishes job to Kafka topic: video-transcode-jobs

Transcoding Worker (GPU instance):
  - Pulls job from Kafka
  - Downloads raw video from S3
  - FFmpeg transcodes to multiple resolutions:
      ffmpeg -i input.mp4
        -vf scale=1280:720 -c:v libx264 -crf 23 output_720p.mp4
        -vf scale=640:480  -c:v libx264 -crf 23 output_480p.mp4
        -vf scale=640:360  -c:v libx264 -crf 23 output_360p.mp4
  - Packages as HLS (segmented .ts files + .m3u8 manifests):
      ffmpeg -i output_720p.mp4 -hls_time 6 -hls_list_size 0 720p.m3u8
  - Uploads all segments to S3: s3://processed-videos/{video_id}/720p/
  - Publishes completion event to Kafka

HLS output structure:
  master.m3u8           → points to bitrate-specific manifests
  720p/720p.m3u8        → lists .ts segment files
  720p/segment_000.ts   → 6-second video chunk
  720p/segment_001.ts
  ...
```

## Transcoding Time Budget

```
5-minute video (50 MB):
  Real-time decode/encode ratio: ~1:3 (3 min encode on 1 CPU)
  GPU acceleration (NVENC): ~1:15 (20 sec encode per resolution)
  5 resolutions × 20 sec = 100 sec total

Target: < 5 min end-to-end
  Upload: ~1 min
  Transcode (parallel on 5 workers): ~2 min  
  Upload segments to S3: ~1 min
  CDN propagation: ~1 min
  Total: ≈ 5 min  ✓
```

## Scaling the Transcoding Farm

```
5 M uploads/day ÷ 86400 sec = 58 uploads/sec
Each upload needs 100 sec of GPU time
GPU workers needed: 58 × 100 / worker_capacity

If 1 GPU worker processes 10 concurrent transcodes:
  Workers = 58 × 100 / 10 = 580 GPU workers

Use auto-scaling:
  SQS queue depth → scale GPU fleet up/down
  Spot instances for cost reduction (~70% cheaper)
```
