"""Abstract NepseClient interface + backend factory.

Skills depend on the interface, never on a specific backend:

    from common.nepse import NepseClient
    client = NepseClient.create()                  # picks backend from $NEPSE_BACKEND
    client = NepseClient.create(backend="nepalstock")  # explicit

Two backends ship with the foundation:
  - "nepalstock"  → thin scraper of nepalstock.com.np
  - "community"   → wraps an existing community Python library (lazy import)

A third backend (MCP) can be added later without changing this interface
or any skill code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Protocol, runtime_checkable

from common.nepse._config import NepseConfigError  # re-export

__all__ = [
    "NepseClient",
    "NepseConfigError",
    "Security",
    "Ohlcv",
    "Fundamentals",
]


# ---- value types ----------------------------------------------------------


@dataclass(frozen=True)
class Security:
    symbol: str
    name: str
    sector_id: str           # matches Registry.sectors[].id
    listed: bool = True
    margin_eligible: bool = False


@dataclass(frozen=True)
class Ohlcv:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    prev_close: float | None = None    # useful for circuit checks


@dataclass(frozen=True)
class Fundamentals:
    symbol: str
    fiscal_year: str          # e.g. "2082/83"
    quarter: int              # 1..4 (Nepali FY quarter)
    reported_at: date | None
    revenue_npr: float | None
    net_income_npr: float | None
    eps_npr: float | None
    book_value_npr: float | None
    raw: dict | None = None        # backend-specific payload pass-through


# ---- abstract interface ---------------------------------------------------


@runtime_checkable
class NepseBackend(Protocol):
    """Minimal contract every backend must implement.

    Methods may raise NotImplementedError for optional capabilities
    (floorsheet, fundamentals) — callers must handle that.
    """

    name: str

    def list_constituents(self) -> list[Security]: ...

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[Ohlcv]: ...

    def get_index(self, index_name: str, start: date, end: date) -> list[Ohlcv]: ...

    def get_quote(self, symbol: str) -> Ohlcv | None: ...   # latest snapshot

    def get_floorsheet(self, day: date) -> list[dict] | None: ...

    def get_fundamentals(self, symbol: str) -> Fundamentals | None: ...


# ---- factory --------------------------------------------------------------


class NepseClient:
    """Backend-agnostic facade. Pick a backend via `create()`."""

    DEFAULT_BACKEND = "nepalstock"

    def __init__(self, backend: NepseBackend):
        self._backend = backend

    @property
    def backend_name(self) -> str:
        return self._backend.name

    @classmethod
    def create(cls, *, backend: str | None = None) -> NepseClient:
        name = (backend or os.environ.get("NEPSE_BACKEND") or cls.DEFAULT_BACKEND).lower()
        if name in ("nepalstock", "scraper"):
            from common.nepse.backends.nepalstock_scraper import NepalstockScraperBackend
            return cls(NepalstockScraperBackend())
        if name in ("community", "community_lib", "lib"):
            from common.nepse.backends.community_lib import CommunityLibBackend
            return cls(CommunityLibBackend())
        raise NepseConfigError(
            f"Unknown NEPSE backend: {name!r}. Supported: 'nepalstock', 'community'."
        )

    # ---- pass-through methods (a thin facade so we can add logging
    # / cache invalidation / metric counters without touching backends) ---

    def list_constituents(self) -> list[Security]:
        return self._backend.list_constituents()

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[Ohlcv]:
        return self._backend.get_ohlcv(symbol, start, end)

    def get_index(self, index_name: str, start: date, end: date) -> list[Ohlcv]:
        return self._backend.get_index(index_name, start, end)

    def get_quote(self, symbol: str) -> Ohlcv | None:
        return self._backend.get_quote(symbol)

    def get_floorsheet(self, day: date) -> list[dict] | None:
        return self._backend.get_floorsheet(day)

    def get_fundamentals(self, symbol: str) -> Fundamentals | None:
        return self._backend.get_fundamentals(symbol)
