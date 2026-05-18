"""Backend B — wraps a third-party Python library for NEPSE data.

This backend deliberately does NOT add a hard dependency on any
particular community library, because the most active candidates
(`nepse-api`, `NepseAPI`, etc.) come and go. Instead it lazy-imports
at construction time and raises a clear error telling the user how
to install whichever one they prefer.

The intent: the scraper backend is primary; this exists so the user
can swap in a community library when the scraper breaks (e.g. after
a nepalstock.com.np redesign) without writing new code.

Implementation pattern: detect which library is available and adapt.
The first matching library wins.

SUPPORTED libraries (in priority order):
  - `nepse_api`           https://pypi.org/project/nepse-api/
  - `Nepse`               various community packages exporting class Nepse
"""

from __future__ import annotations

from datetime import date
from typing import Any

from common.nepse.client import Fundamentals, Ohlcv, Security


class CommunityLibBackend:
    name = "community"

    def __init__(self):
        self._impl: Any | None = self._import_first_available()
        if self._impl is None:
            raise ImportError(
                "No supported NEPSE community library is installed. Install one of:\n"
                "    pip install nepse-api\n"
                "Or use the default scraper backend instead "
                "(unset NEPSE_BACKEND or set it to 'nepalstock')."
            )

    @staticmethod
    def _import_first_available() -> Any | None:
        try:
            import nepse_api  # type: ignore
        except ImportError:
            pass
        else:
            return nepse_api

        try:
            from Nepse import Nepse as _N  # type: ignore
            return _N()
        except ImportError:
            pass

        return None

    # ---- interface methods --------------------------------------------------
    #
    # Each method is a thin adapter from the active library's surface area
    # onto our value objects. Library APIs differ; we keep the adapters
    # together so a single library's quirks live in one place.

    def list_constituents(self) -> list[Security]:
        impl = self._impl
        getter = getattr(impl, "get_company_list", None) or getattr(impl, "list_securities", None)
        if getter is None:
            return []
        rows = getter() or []
        return [self._adapt_security(row) for row in rows]

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[Ohlcv]:
        impl = self._impl
        getter = (
            getattr(impl, "get_historical_data", None)
            or getattr(impl, "get_history", None)
            or getattr(impl, "get_ohlc", None)
        )
        if getter is None:
            return []
        rows = getter(symbol, start.isoformat(), end.isoformat()) or []
        return [self._adapt_ohlcv(row) for row in rows]

    def get_index(self, index_name: str, start: date, end: date) -> list[Ohlcv]:
        impl = self._impl
        getter = getattr(impl, "get_index_history", None)
        if getter is None:
            return []
        rows = getter(index_name, start.isoformat(), end.isoformat()) or []
        return [self._adapt_ohlcv(row) for row in rows]

    def get_quote(self, symbol: str) -> Ohlcv | None:
        impl = self._impl
        getter = getattr(impl, "get_price_volume", None) or getattr(impl, "get_quote", None)
        if getter is None:
            return None
        row = getter(symbol)
        return self._adapt_ohlcv(row) if row else None

    def get_floorsheet(self, day: date) -> list[dict] | None:
        impl = self._impl
        getter = getattr(impl, "get_floorsheet", None)
        if getter is None:
            return None
        return getter(day.isoformat())

    def get_fundamentals(self, symbol: str) -> Fundamentals | None:
        # Most community libraries don't expose structured fundamentals.
        return None

    # ---- adapters ----------------------------------------------------------

    @staticmethod
    def _adapt_security(row: dict) -> Security:
        symbol = str(row.get("symbol") or row.get("ticker") or "").upper()
        return Security(
            symbol=symbol,
            name=str(row.get("name") or row.get("securityName") or ""),
            sector_id=str(row.get("sector_id") or row.get("sector") or "OTHERS").upper(),
            listed=bool(row.get("listed", True)),
            margin_eligible=bool(row.get("margin_eligible", False)),
        )

    @staticmethod
    def _adapt_ohlcv(row: dict) -> Ohlcv:
        return Ohlcv(
            day=date.fromisoformat(str(row.get("date"))[:10]),
            open=float(row.get("open") or 0.0),
            high=float(row.get("high") or 0.0),
            low=float(row.get("low") or 0.0),
            close=float(row.get("close") or 0.0),
            volume=int(row.get("volume") or 0),
            prev_close=(
                float(row["prev_close"]) if row.get("prev_close") is not None else None
            ),
        )
