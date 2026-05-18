"""Shared HTTP helper — rate limiting + retry + cache integration.

Both backends use this so they share the same throttling / retry policy
and never compete for the rate-limited NEPSE endpoint.
"""

from __future__ import annotations

import sys
import time
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

from common.nepse.cache import NepseCache

# Conservative defaults — NEPSE doesn't publish formal limits but
# community libraries cap at 6 req/min. We use ~30 req/min as a ceiling.
DEFAULT_MIN_INTERVAL_S = 2.0
DEFAULT_TIMEOUT_S = 30
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF_S = 5.0
DEFAULT_USER_AGENT = "claude-trading-skills/0.1 (+https://github.com/)"


class HttpClient:
    """Thin requests.Session wrapper. Backend-agnostic.

    `verify=False` disables TLS certificate verification. Only useful as
    an escape hatch when a server presents a misconfigured cert chain
    (e.g. missing intermediate). The data we fetch is public market data,
    so the practical risk is bounded — but a MITM attacker could feed
    false prices. Use at your own discretion.
    """

    def __init__(
        self,
        *,
        cache: NepseCache | None = None,
        min_interval_s: float = DEFAULT_MIN_INTERVAL_S,
        timeout_s: int = DEFAULT_TIMEOUT_S,
        retries: int = DEFAULT_RETRIES,
        user_agent: str = DEFAULT_USER_AGENT,
        verify: bool = True,
    ):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.session.verify = verify
        self.cache = cache or NepseCache()
        self.min_interval_s = min_interval_s
        self.timeout_s = timeout_s
        self.retries = retries
        self._last_call_ts = 0.0
        self.calls_made = 0

    def get_json(
        self,
        url: str,
        *,
        params: dict | None = None,
        namespace: str,
        ttl_seconds: int,
    ) -> Any | None:
        """GET → JSON with cache + rate limit + retry.

        Returns None on permanent failure.
        """
        cached = self.cache.get(namespace, url, params, ttl_seconds=ttl_seconds)
        if cached is not None:
            return cached

        for attempt in range(self.retries + 1):
            self._throttle()
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout_s)
                self.calls_made += 1
            except requests.RequestException as exc:
                if attempt == self.retries:
                    print(f"ERROR: GET {url} failed: {exc}", file=sys.stderr)
                    return None
                time.sleep(DEFAULT_BACKOFF_S)
                continue

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError:
                    print(f"ERROR: GET {url} returned non-JSON", file=sys.stderr)
                    return None
                self.cache.put(namespace, url, params, data)
                return data

            if resp.status_code in (429, 503) and attempt < self.retries:
                wait = DEFAULT_BACKOFF_S * (attempt + 1)
                print(
                    f"WARN: GET {url} got {resp.status_code}; backing off {wait}s",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue

            print(
                f"ERROR: GET {url} failed: {resp.status_code} {resp.text[:200]}",
                file=sys.stderr,
            )
            return None
        return None

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call_ts
        if elapsed < self.min_interval_s:
            time.sleep(self.min_interval_s - elapsed)
        self._last_call_ts = time.time()
