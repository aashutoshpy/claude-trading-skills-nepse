"""Disk-backed response cache shared across NEPSE backends.

Why on-disk: NEPSE rate limits are tight (~6 req/min on community MCP,
unknown but throttled on nepalstock.com.np). Batch screeners that touch
all 284 names benefit hugely from persisting OHLCV between runs.

TTL is per cache key, picked by the caller (e.g. universe lists for 24h,
EOD bars for 12h, intraday for 60s). The cache is keyed on a full URL +
params hash so two backends asking for "AAPL EOD" do not collide.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path(tempfile.gettempdir()) / "nepse_cache"


class NepseCache:
    def __init__(self, cache_dir: Path | None = None):
        self.dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _key(namespace: str, url: str, params: dict | None = None) -> str:
        canonical = json.dumps({"url": url, "params": params or {}}, sort_keys=True)
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:24]
        # Limit namespace to keep filenames sane
        safe_ns = "".join(c if c.isalnum() else "_" for c in namespace)[:48]
        return f"{safe_ns}_{digest}.json"

    def _path(self, key: str) -> Path:
        return self.dir / key

    def get(
        self, namespace: str, url: str, params: dict | None = None, *, ttl_seconds: int
    ) -> Any | None:
        path = self._path(self._key(namespace, url, params))
        if not path.exists():
            return None
        if ttl_seconds > 0 and (time.time() - path.stat().st_mtime) > ttl_seconds:
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None

    def put(self, namespace: str, url: str, params: dict | None, value: Any) -> None:
        path = self._path(self._key(namespace, url, params))
        # Atomic write: write to tmp, then rename.
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(value, fh)
        os.replace(tmp, path)

    def clear(self) -> int:
        """Remove all cache entries. Returns count removed."""
        n = 0
        for f in self.dir.glob("*.json"):
            try:
                f.unlink()
                n += 1
            except OSError:
                pass
        return n
