"""Tests for the nepalstock scraper backend.

These tests do NOT hit the network — they inject a fake HttpClient
that returns recorded fixture responses.
"""

from datetime import date
from typing import Any, Optional

import pytest

from common.nepse._config import reset_cache
from common.nepse.backends.nepalstock_scraper import (
    NepalstockScraperBackend,
    _normalize_sector,
    _parse_ohlcv_row,
    _parse_security,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_cache()
    yield
    reset_cache()


class FakeHttp:
    """Stub for the HttpClient — returns canned JSON, records calls."""

    def __init__(self, responses: dict[str, Any]):
        self.responses = responses
        self.calls: list[tuple[str, Optional[dict]]] = []

    def get_json(self, url, *, params=None, namespace, ttl_seconds):
        self.calls.append((url, params))
        # Look up by URL suffix so callers don't need to know the full URL
        for suffix, body in self.responses.items():
            if url.endswith(suffix):
                return body
        return None


# ---- sector normalization (pure functions) --------------------------------


def test_normalize_sector_handles_known_labels():
    assert _normalize_sector("Commercial Banks") == "BANKING"
    assert _normalize_sector("Hydro Power") == "HYDROPOWER"
    assert _normalize_sector("HYDROPOWER") == "HYDROPOWER"
    assert _normalize_sector("Non Life Insurance") == "NON_LIFE_INSURANCE"
    assert _normalize_sector("Microfinance") == "MICROFINANCE"


def test_normalize_sector_falls_back_to_others_for_unknown():
    assert _normalize_sector("Something Brand New") == "OTHERS"


# ---- row parsers ----------------------------------------------------------


def test_parse_security_uses_margin_set():
    row = {"id": 131, "symbol": "NABIL", "securityName": "Nabil Bank", "instrumentType": "Commercial Banks"}
    sec = _parse_security(row, frozenset({"NABIL"}))
    assert sec.symbol == "NABIL"
    assert sec.sector_id == "BANKING"
    assert sec.margin_eligible is True
    # The backend attaches the raw security id for later lookups
    assert getattr(sec, "_raw_id", None) == 131


def test_parse_security_not_margin_eligible_when_absent():
    row = {"id": 999, "symbol": "FAKE", "securityName": "Fake Co", "instrumentType": "Others"}
    sec = _parse_security(row, frozenset({"NABIL"}))
    assert sec.margin_eligible is False


def test_parse_ohlcv_row_with_canonical_field_names():
    row = {
        "date": "2026-05-15",
        "open": 100.0,
        "high": 105.0,
        "low": 98.0,
        "close": 103.0,
        "volume": 1000,
        "previousClose": 99.0,
    }
    o = _parse_ohlcv_row(row)
    assert o.day == date(2026, 5, 15)
    assert o.open == 100.0
    assert o.close == 103.0
    assert o.volume == 1000
    assert o.prev_close == 99.0


def test_parse_ohlcv_row_handles_alternate_field_names():
    row = {
        "date": "2026-05-15T00:00:00",
        "openPrice": 100.0,
        "highPrice": 105.0,
        "lowPrice": 98.0,
        "closePrice": 103.0,
        "totalTradedQuantity": 555,
    }
    o = _parse_ohlcv_row(row)
    assert o.day == date(2026, 5, 15)
    assert o.open == 100.0
    assert o.volume == 555
    assert o.prev_close is None


# ---- backend integration with FakeHttp ------------------------------------


def test_list_constituents_parses_paged_response():
    backend = NepalstockScraperBackend(
        http=FakeHttp(
            {
                "/nots/security": {
                    "content": [
                        {"id": 131, "symbol": "NABIL", "securityName": "Nabil Bank",
                         "instrumentType": "Commercial Banks"},
                        {"id": 274, "symbol": "UPPER", "securityName": "Upper Tamakoshi",
                         "instrumentType": "Hydro Power"},
                    ]
                }
            }
        )
    )
    secs = backend.list_constituents()
    assert [s.symbol for s in secs] == ["NABIL", "UPPER"]
    assert secs[0].sector_id == "BANKING"
    assert secs[1].sector_id == "HYDROPOWER"


def test_list_constituents_empty_when_endpoint_missing():
    backend = NepalstockScraperBackend(http=FakeHttp({}))
    assert backend.list_constituents() == []


def test_get_fundamentals_returns_none_by_design():
    backend = NepalstockScraperBackend(http=FakeHttp({}))
    assert backend.get_fundamentals("NABIL") is None
