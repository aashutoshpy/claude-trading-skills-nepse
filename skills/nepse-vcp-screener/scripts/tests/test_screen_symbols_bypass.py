"""Verifies `screen(--symbols)` works even when `list_constituents()` fails.

The default `nepalstock` backend can be unreachable (network down, expired
TLS cert chain on nepalstock.com.np, NEPSE site redesign). In that case the
user can still screen a small, known set of names via `--symbols X Y Z` —
the screener should NOT abort on the universe-fetch failure, but instead
fall back to synthesizing minimal Security stubs from the requested
symbols and continue.
"""

from datetime import date, timedelta

import pytest
from screen_nepse_vcp import screen
from vcp_detector import VcpParameters

from common.nepse._config import reset_cache
from common.nepse.client import Ohlcv, Security
from common.nepse.registry import Registry


@pytest.fixture(autouse=True)
def _reset_registry_cache():
    reset_cache()
    yield
    reset_cache()


def _make_uptrend_bars(days: int = 240, start: float = 100.0, slope: float = 0.4) -> list[Ohlcv]:
    bars = []
    d0 = date(2025, 1, 1)
    for i in range(days):
        close = start + slope * i
        bars.append(
            Ohlcv(
                day=d0 + timedelta(days=i),
                open=close - 0.2,
                high=close + 0.3,
                low=close - 0.3,
                close=close,
                volume=10_000,
            )
        )
    return bars


class _ConstituentsErrorClient:
    """Backend that fails on list_constituents() but serves OHLCV per-symbol."""

    def list_constituents(self) -> list[Security]:
        raise ConnectionError("simulated backend failure (e.g., TLS cert chain)")

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[Ohlcv]:
        return _make_uptrend_bars()


class _EmptyConstituentsClient:
    """Backend that returns an empty universe (e.g., scraper drift)."""

    def list_constituents(self) -> list[Security]:
        return []

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[Ohlcv]:
        return _make_uptrend_bars()


def test_symbols_bypass_when_list_constituents_raises(capsys):
    registry = Registry.load()
    rows = screen(
        client=_ConstituentsErrorClient(),
        registry=registry,
        symbols=["NABIL", "UPPER", "NICA"],
        history_days=300,
        params=VcpParameters(),
        top_n=20,
    )
    # The screener didn't crash; OHLCV was still fetched per-symbol.
    # The synthetic bars are a pure uptrend with no VCP base, so 0 valid
    # candidates is the expected outcome — what we care about is that
    # the run didn't abort with "ERROR: no NEPSE constituents to screen".
    err = capsys.readouterr().err
    assert "list_constituents() unavailable" in err
    assert "no NEPSE constituents to screen" not in err
    # rows can be 0 (no VCP setups in uptrend) — that's fine.
    assert isinstance(rows, list)


def test_symbols_bypass_when_list_constituents_returns_empty(capsys):
    registry = Registry.load()
    rows = screen(
        client=_EmptyConstituentsClient(),
        registry=registry,
        symbols=["NABIL", "UPPER"],
        history_days=300,
        params=VcpParameters(),
        top_n=20,
    )
    err = capsys.readouterr().err
    # No "WARN: list_constituents() unavailable" (it returned [], didn't raise)
    # but no "ERROR: no NEPSE constituents to screen" either — fell back to stubs.
    assert "no NEPSE constituents to screen" not in err
    assert isinstance(rows, list)


def test_no_symbols_still_fails_loudly_when_universe_empty(capsys):
    registry = Registry.load()
    # When --symbols is NOT given, an empty universe IS an error.
    rows = screen(
        client=_EmptyConstituentsClient(),
        registry=registry,
        symbols=None,
        history_days=300,
        params=VcpParameters(),
        top_n=20,
    )
    err = capsys.readouterr().err
    assert "no NEPSE constituents to screen" in err
    assert rows == []
