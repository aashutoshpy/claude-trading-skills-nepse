"""nepalstock.com.np backend — thin scraper, no third-party API.

This is the primary backend (no external dependency, full control).
The site occasionally changes its HTML/JSON endpoints; the request
shapes here are documented per-method so they can be updated when
that happens.

Endpoint discovery:
  - The site uses an internal JSON API at https://www.nepalstock.com.np/api/...
    that powers its public dashboards. We use those JSON endpoints
    where possible, fall back to HTML scraping otherwise.
  - All endpoints are GET; no auth required for public market data.

This backend never reaches the network from tests — tests inject a
fake HttpClient via the constructor.
"""

from __future__ import annotations

from datetime import date

from common.nepse.backends._http import HttpClient
from common.nepse.client import Fundamentals, Ohlcv, Security
from common.nepse.registry import Registry

_BASE = "https://www.nepalstock.com.np/api"

# TTLs — tuned for the type of data:
_TTL_CONSTITUENTS = 24 * 3600   # universe changes rarely
_TTL_EOD = 12 * 3600            # historical OHLCV is stable
_TTL_QUOTE = 60                 # latest snapshot
_TTL_INDEX = 12 * 3600
_TTL_FLOORSHEET = 12 * 3600


class NepalstockScraperBackend:
    name = "nepalstock"

    def __init__(self, *, http: HttpClient | None = None):
        self.http = http or HttpClient()
        # Registry is YAML-driven (deterministic + offline) — useful when
        # the universe endpoint is down or rate-limited.
        try:
            self._registry: Registry | None = Registry.load()
        except Exception:
            self._registry = None

    # ---- universe ---------------------------------------------------------

    def list_constituents(self) -> list[Security]:
        # Endpoint shape (subject to change): GET /api/nots/security?nonDelisted=true
        # Returns a paged JSON array of `{symbol, securityName, sector, ...}`.
        data = self.http.get_json(
            f"{_BASE}/nots/security",
            params={"nonDelisted": "true"},
            namespace="constituents",
            ttl_seconds=_TTL_CONSTITUENTS,
        )
        if not data:
            return []
        margin_set = self._registry.margin_eligible_symbols if self._registry else frozenset()
        return [_parse_security(row, margin_set) for row in _iter_rows(data) if row.get("symbol")]

    # ---- OHLCV -----------------------------------------------------------

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[Ohlcv]:
        # Endpoint shape: /api/nots/market/graphdata/{security_id}?startDate=&endDate=
        # The site uses numeric security_id; we look it up via constituents.
        sec_id = self._lookup_security_id(symbol)
        if sec_id is None:
            return []
        data = self.http.get_json(
            f"{_BASE}/nots/market/graphdata/{sec_id}",
            params={"startDate": start.isoformat(), "endDate": end.isoformat()},
            namespace=f"ohlcv_{symbol.upper()}",
            ttl_seconds=_TTL_EOD,
        )
        if not data:
            return []
        return [_parse_ohlcv_row(row) for row in _iter_rows(data) if row.get("date")]

    def get_index(self, index_name: str, start: date, end: date) -> list[Ohlcv]:
        # /api/nots/graph/index/{index_id} — index IDs (1 = NEPSE, etc.)
        index_id = _INDEX_IDS.get(index_name.upper())
        if index_id is None:
            return []
        data = self.http.get_json(
            f"{_BASE}/nots/graph/index/{index_id}",
            params={"startDate": start.isoformat(), "endDate": end.isoformat()},
            namespace=f"index_{index_name.upper()}",
            ttl_seconds=_TTL_INDEX,
        )
        if not data:
            return []
        return [_parse_ohlcv_row(row) for row in _iter_rows(data) if row.get("date")]

    def get_quote(self, symbol: str) -> Ohlcv | None:
        sec_id = self._lookup_security_id(symbol)
        if sec_id is None:
            return None
        data = self.http.get_json(
            f"{_BASE}/nots/security/{sec_id}",
            params=None,
            namespace=f"quote_{symbol.upper()}",
            ttl_seconds=_TTL_QUOTE,
        )
        if not data:
            return None
        return _parse_ohlcv_row(data) if data.get("date") else None

    # ---- optional capabilities -------------------------------------------

    def get_floorsheet(self, day: date) -> list[dict] | None:
        # Floorsheet is large; pagination required in practice.
        data = self.http.get_json(
            f"{_BASE}/nots/nepse-data/floorsheet",
            params={"businessDate": day.isoformat(), "size": 500, "sort": "contractId,desc"},
            namespace=f"floorsheet_{day.isoformat()}",
            ttl_seconds=_TTL_FLOORSHEET,
        )
        if data is None:
            return None
        return list(_iter_rows(data))

    def get_fundamentals(self, symbol: str) -> Fundamentals | None:
        # nepalstock.com.np does not expose structured fundamentals.
        # Skills that need fundamentals should fall back to manual CSV
        # ingestion or use the community backend if available.
        return None

    # ---- internal --------------------------------------------------------

    def _lookup_security_id(self, symbol: str) -> int | None:
        # In a live deployment we cache symbol→id from list_constituents();
        # for now we rely on the constituents endpoint each time. This is
        # cached aggressively (24h TTL).
        for sec in self.list_constituents():
            if sec.symbol.upper() == symbol.upper():
                raw_id = getattr(sec, "_raw_id", None)
                if raw_id is not None:
                    return raw_id
        return None


# ---- helpers --------------------------------------------------------------


_INDEX_IDS = {
    "NEPSE": 58,           # placeholder ids; correct values must be verified
    "BANKING": 51,         # against the live site before relying on them.
    "HYDROPOWER": 57,
    "DEVELOPMENT_BANK": 52,
    "FINANCE": 53,
    "MICROFINANCE": 60,
    "LIFE_INSURANCE": 62,
    "NON_LIFE_INSURANCE": 63,
    "HOTELS": 55,
    "MANUFACTURING": 56,
    "TRADING": 54,
    "MUTUAL_FUNDS": 64,
    "INVESTMENT": 65,
    "OTHERS": 59,
}


def _iter_rows(data) -> list[dict]:
    """nepalstock JSON sometimes wraps payloads in `{content: [...]}` (Spring
    page) and sometimes returns a raw list. Normalize both."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "content" in data and isinstance(data["content"], list):
            return data["content"]
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
        # single-record response
        return [data]
    return []


def _parse_security(row: dict, margin_set: frozenset[str]) -> Security:
    symbol = str(row.get("symbol", "")).upper()
    sec = Security(
        symbol=symbol,
        name=str(row.get("securityName") or row.get("name") or ""),
        sector_id=_normalize_sector(row.get("instrumentType") or row.get("sectorName") or ""),
        listed=not row.get("isDelisted", False),
        margin_eligible=symbol in margin_set,
    )
    # Attach raw id as a private attribute (Security is frozen so we use
    # object.__setattr__). This is best-effort — backend-internal.
    raw_id = row.get("id") or row.get("securityId")
    if raw_id is not None:
        object.__setattr__(sec, "_raw_id", int(raw_id))
    return sec


def _normalize_sector(label: str) -> str:
    """Map nepalstock.com.np sector labels onto Registry sector IDs."""
    lookup = {
        "commercial banks": "BANKING",
        "development banks": "DEVELOPMENT_BANK",
        "finance": "FINANCE",
        "microfinance": "MICROFINANCE",
        "hydro power": "HYDROPOWER",
        "hydropower": "HYDROPOWER",
        "life insurance": "LIFE_INSURANCE",
        "non life insurance": "NON_LIFE_INSURANCE",
        "non-life insurance": "NON_LIFE_INSURANCE",
        "hotels": "HOTELS",
        "hotels and tourism": "HOTELS",
        "manufacturing and processing": "MANUFACTURING",
        "manufacturing & processing": "MANUFACTURING",
        "tradings": "TRADING",
        "trading": "TRADING",
        "mutual fund": "MUTUAL_FUNDS",
        "mutual funds": "MUTUAL_FUNDS",
        "investment": "INVESTMENT",
        "others": "OTHERS",
    }
    return lookup.get(label.strip().lower(), "OTHERS")


def _parse_ohlcv_row(row: dict) -> Ohlcv:
    return Ohlcv(
        day=date.fromisoformat(str(row["date"])[:10]),
        open=float(row.get("open") or row.get("openPrice") or 0.0),
        high=float(row.get("high") or row.get("highPrice") or 0.0),
        low=float(row.get("low") or row.get("lowPrice") or 0.0),
        close=float(row.get("close") or row.get("closePrice") or 0.0),
        volume=int(row.get("volume") or row.get("totalTradedQuantity") or 0),
        prev_close=(
            float(row["previousClose"]) if row.get("previousClose") is not None else None
        ),
    )

