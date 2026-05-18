"""Pure-functional NEPSE dividend / value scoring.

No I/O. The CLI loads the CSV and OHLCV; this module takes the assembled
inputs and returns ranked candidate dicts.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from statistics import mean

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv, Security

NEPSE_FACE_VALUE = 100.0   # NPR per share, by convention


@dataclass
class DividendRecord:
    symbol: str
    cash_div_pct: float
    bonus_div_pct: float
    reported_at: str | None = None

    @property
    def total_div_pct(self) -> float:
        return self.cash_div_pct + self.bonus_div_pct


def parse_dividends_csv(text: str) -> dict[str, DividendRecord]:
    """Parse a CSV with columns: symbol, cash_div_pct, bonus_div_pct, [reported_at].

    Unknown columns are ignored; missing optional fields default to 0 / None.
    Rows with no symbol are silently skipped.
    """
    out: dict[str, DividendRecord] = {}
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        symbol = (row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        try:
            cash = float(row.get("cash_div_pct") or 0.0)
            bonus = float(row.get("bonus_div_pct") or 0.0)
        except ValueError:
            continue
        out[symbol] = DividendRecord(
            symbol=symbol,
            cash_div_pct=cash,
            bonus_div_pct=bonus,
            reported_at=(row.get("reported_at") or "").strip() or None,
        )
    return out


def _sma(bars: list[Ohlcv], window: int) -> float | None:
    if len(bars) < window:
        return None
    return mean(b.close for b in bars[-window:])


def _distance_to_sma200_pct(bars: list[Ohlcv]) -> float | None:
    sma200 = _sma(bars, 200)
    if sma200 is None or sma200 <= 0:
        return None
    return round((bars[-1].close - sma200) / sma200 * 100.0, 2)


def yield_for(record: DividendRecord, price: float) -> float | None:
    if price <= 0:
        return None
    return round(record.total_div_pct * NEPSE_FACE_VALUE / price, 2)


def score_universe(
    securities: list[Security],
    *,
    bars_by_symbol: dict[str, list[Ohlcv]],
    dividends: dict[str, DividendRecord],
    min_yield_pct: float = 5.0,
) -> list[dict]:
    """Return a list of candidate dicts sorted by yield (desc).

    Names with no dividend record are EXCLUDED — we don't fabricate
    yield estimates from OHLCV in this version.
    """
    candidates: list[dict] = []
    for sec in securities:
        record = dividends.get(sec.symbol.upper())
        if record is None:
            continue
        bars = bars_by_symbol.get(sec.symbol.upper())
        if not bars:
            continue
        bars = sorted(bars, key=lambda b: b.day)
        price = bars[-1].close
        y = yield_for(record, price)
        if y is None or y < min_yield_pct:
            continue
        candidates.append(
            {
                "symbol": sec.symbol,
                "sector": sec.sector_id,
                "price": round(price, 2),
                "cash_div_pct": record.cash_div_pct,
                "bonus_div_pct": record.bonus_div_pct,
                "total_div_pct": round(record.total_div_pct, 2),
                "yield_pct": y,
                "distance_to_sma200_pct": _distance_to_sma200_pct(bars),
                "margin_eligible": sec.margin_eligible,
                "dividend_reported_at": record.reported_at,
            }
        )
    candidates.sort(key=lambda r: r["yield_pct"], reverse=True)
    return candidates
