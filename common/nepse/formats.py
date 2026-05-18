"""NPR formatting + price-band helpers."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from common.nepse._config import load_rules


def format_npr(amount: float | int | Decimal, *, with_symbol: bool = True, decimals: int = 2) -> str:
    """Format an amount as Nepali Rupees with thousands separators.

    >>> format_npr(1234567.89)
    'NPR 1,234,567.89'
    >>> format_npr(425.0, decimals=0)
    'NPR 425'
    """
    quant = Decimal(10) ** -decimals
    rounded = Decimal(str(amount)).quantize(quant, rounding=ROUND_HALF_UP)
    text = f"{rounded:,.{decimals}f}"
    return f"NPR {text}" if with_symbol else text


def daily_price_band_pct() -> float:
    """Current daily price-fluctuation limit (15.0% as of 2026-04-17)."""
    return float(load_rules()["daily_price_band_pct"])


def upper_circuit_price(prev_close: float) -> float:
    """Highest legal trade price for a regular-session order."""
    band = daily_price_band_pct() / 100.0
    return round(prev_close * (1.0 + band), 2)


def lower_circuit_price(prev_close: float) -> float:
    """Lowest legal trade price for a regular-session order."""
    band = daily_price_band_pct() / 100.0
    return round(prev_close * (1.0 - band), 2)


def at_circuit(price: float, prev_close: float, *, tolerance: float = 0.005) -> str | None:
    """Return 'upper' / 'lower' if `price` is at the circuit, else None."""
    upper = upper_circuit_price(prev_close)
    lower = lower_circuit_price(prev_close)
    if abs(price - upper) <= tolerance:
        return "upper"
    if abs(price - lower) <= tolerance:
        return "lower"
    return None
