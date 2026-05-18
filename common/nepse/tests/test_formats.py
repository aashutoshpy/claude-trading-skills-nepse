"""Tests for NPR formatting and circuit-price helpers."""

import pytest

from common.nepse._config import reset_cache
from common.nepse.formats import (
    at_circuit,
    daily_price_band_pct,
    format_npr,
    lower_circuit_price,
    upper_circuit_price,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_cache()
    yield
    reset_cache()


# ---- formatting -----------------------------------------------------------


def test_format_npr_with_symbol_and_thousands_separator():
    assert format_npr(1234567.89) == "NPR 1,234,567.89"


def test_format_npr_zero_decimals():
    assert format_npr(425.0, decimals=0) == "NPR 425"


def test_format_npr_without_symbol():
    assert format_npr(100.0, with_symbol=False) == "100.00"


def test_format_npr_handles_small_amounts():
    assert format_npr(0.5) == "NPR 0.50"


# ---- circuit prices -------------------------------------------------------


def test_daily_price_band_is_15_percent_post_april_2026():
    # Regression: if someone reverts config to 10%, this catches it
    assert daily_price_band_pct() == 15.0


def test_upper_circuit_price_uses_15_percent_band():
    # prev close 100 → upper 115.00
    assert upper_circuit_price(100.0) == 115.0


def test_lower_circuit_price_uses_15_percent_band():
    # prev close 100 → lower 85.00
    assert lower_circuit_price(100.0) == 85.0


def test_at_circuit_detects_upper():
    assert at_circuit(115.0, 100.0) == "upper"


def test_at_circuit_detects_lower():
    assert at_circuit(85.0, 100.0) == "lower"


def test_at_circuit_returns_none_for_mid_range():
    assert at_circuit(105.0, 100.0) is None
