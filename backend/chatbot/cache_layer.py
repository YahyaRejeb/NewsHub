from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


class DiskTTLCache:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get(self, namespace: str, key: str) -> Any | None:
        path = self._path_for(namespace, key)
        if not path.exists():
            return None

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        expires_at = payload.get("expires_at")
        if expires_at is not None and expires_at < time.time():
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            return None

        return payload.get("value")

    def set(self, namespace: str, key: str, value: Any, ttl_seconds: int) -> Any:
        namespace_dir = self.base_dir / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)

        path = self._path_for(namespace, key)
        temp_path = path.with_suffix(".tmp")
        payload = {
            "expires_at": time.time() + ttl_seconds,
            "value": value,
        }

        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(path)
        return value

    def _path_for(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.base_dir / namespace / f"{digest}.json"
