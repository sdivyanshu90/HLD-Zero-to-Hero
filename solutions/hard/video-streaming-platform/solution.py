from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, List


@dataclass(slots=True)
class Rendition:
    quality: str
    bitrate_kbps: int
    chunks: list[str]


@dataclass(slots=True)
class VideoAsset:
    video_id: str
    title: str
    source_blob: str
    renditions: dict[str, Rendition] = field(default_factory=dict)


class VideoStreamingPlatform:
    def __init__(self) -> None:
        self._videos: Dict[str, VideoAsset] = {}
        self._blob_store: Dict[str, str] = {}
        self._cdn_cache: Dict[str, str] = {}
        self._watch_history: DefaultDict[str, Dict[str, int]] = defaultdict(dict)

    def upload(self, video_id: str, title: str, source_blob: str) -> None:
        self._blob_store[source_blob] = f"source:{title}"
        self._videos[video_id] = VideoAsset(video_id=video_id, title=title, source_blob=source_blob)

    def transcode(self, video_id: str) -> None:
        asset = self._videos[video_id]
        renditions = {
            "360p": Rendition("360p", 800, [f"{video_id}/360p/seg-{index}" for index in range(1, 4)]),
            "720p": Rendition("720p", 2500, [f"{video_id}/720p/seg-{index}" for index in range(1, 4)]),
        }
        asset.renditions = renditions
        for rendition in renditions.values():
            for chunk in rendition.chunks:
                self._blob_store[chunk] = f"bytes:{chunk}"

    def manifest(self, video_id: str) -> dict[str, list[str]]:
        asset = self._videos[video_id]
        return {quality: rendition.chunks for quality, rendition in asset.renditions.items()}

    def stream_chunk(self, video_id: str, quality: str, chunk_index: int) -> str:
        asset = self._videos[video_id]
        chunk_name = asset.renditions[quality].chunks[chunk_index]
        if chunk_name not in self._cdn_cache:
            self._cdn_cache[chunk_name] = self._blob_store[chunk_name]
        return self._cdn_cache[chunk_name]

    def record_watch_progress(self, user_id: str, video_id: str, second_offset: int) -> None:
        self._watch_history[user_id][video_id] = second_offset

    def watch_progress(self, user_id: str, video_id: str) -> int:
        return self._watch_history[user_id].get(video_id, 0)


def main() -> None:
    platform = VideoStreamingPlatform()
    platform.upload("v1", "System Design at Scale", "blob://source/v1")
    platform.transcode("v1")

    print("Manifest:")
    print(platform.manifest("v1"))
    print()
    print("Streamed chunk:")
    print(platform.stream_chunk("v1", "720p", 0))
    platform.record_watch_progress("u1", "v1", 95)
    print("Watch progress:", platform.watch_progress("u1", "v1"))


if __name__ == "__main__":
    main()