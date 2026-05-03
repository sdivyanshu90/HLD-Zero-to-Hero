from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Dict, List, Set


@dataclass(slots=True)
class FileVersion:
    version: int
    chunk_hashes: list[str]


@dataclass(slots=True)
class FileMetadata:
    path: str
    versions: list[FileVersion] = field(default_factory=list)
    shared_with: set[str] = field(default_factory=set)


class DistributedFileStorage:
    def __init__(self, chunk_size: int = 4) -> None:
        self.chunk_size = chunk_size
        self._blob_store: Dict[str, bytes] = {}
        self._metadata: Dict[str, FileMetadata] = {}

    def upload(self, path: str, content: bytes) -> int:
        chunk_hashes: list[str] = []
        for index in range(0, len(content), self.chunk_size):
            chunk = content[index : index + self.chunk_size]
            chunk_hash = sha256(chunk).hexdigest()
            self._blob_store.setdefault(chunk_hash, chunk)
            chunk_hashes.append(chunk_hash)

        metadata = self._metadata.setdefault(path, FileMetadata(path=path))
        version = len(metadata.versions) + 1
        metadata.versions.append(FileVersion(version=version, chunk_hashes=chunk_hashes))
        return version

    def download(self, path: str, version: int | None = None) -> bytes:
        metadata = self._metadata[path]
        file_version = metadata.versions[-1] if version is None else metadata.versions[version - 1]
        return b"".join(self._blob_store[chunk_hash] for chunk_hash in file_version.chunk_hashes)

    def share(self, path: str, user_id: str) -> None:
        self._metadata[path].shared_with.add(user_id)

    def version_history(self, path: str) -> list[int]:
        return [file_version.version for file_version in self._metadata[path].versions]

    def deduplicated_chunk_count(self) -> int:
        return len(self._blob_store)


def main() -> None:
    storage = DistributedFileStorage(chunk_size=5)
    storage.upload("/designs/hld.txt", b"system-design-notes")
    storage.upload("/designs/hld.txt", b"system-design-notes-v2")
    storage.share("/designs/hld.txt", "teammate-1")

    print("versions:", storage.version_history("/designs/hld.txt"))
    print("deduplicated chunks:", storage.deduplicated_chunk_count())
    print("latest content:", storage.download("/designs/hld.txt"))


if __name__ == "__main__":
    main()