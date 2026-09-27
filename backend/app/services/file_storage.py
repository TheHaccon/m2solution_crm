from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol
from uuid import uuid4

UUID_KEY = re.compile(r"^[0-9a-f]{32}$")


class FileStorage(Protocol):
    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes: ...

    def path_for(self, key: str) -> Path: ...

    def delete(self, key: str) -> None: ...


class LocalDiskStorage:
    """Store blobs as FILES_ROOT/<uuid>. Swap later for a Drive-backed impl."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not UUID_KEY.fullmatch(key):
            raise ValueError("invalid storage key")
        return self.root / key

    def new_key(self) -> str:
        return uuid4().hex

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def path_for(self, key: str) -> Path:
        return self._path(key)

    def delete(self, key: str) -> None:
        path = self._path(key)
        path.unlink(missing_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.unlink(missing_ok=True)


def local_storage(root: str) -> LocalDiskStorage:
    return LocalDiskStorage(Path(root))


_storage: LocalDiskStorage | None = None


def get_storage() -> LocalDiskStorage:
    global _storage
    if _storage is None:
        from app.core.config import settings

        _storage = local_storage(settings.files_root)
    return _storage
