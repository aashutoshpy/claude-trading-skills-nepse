"""Pure-functional NEPSE uptrend ratio math.

The uptrend ratio is the % of names trading above their 200-day SMA on
a given date. Computing the historical series requires the 200-day SMA
to be available at each historical point — so we walk forward through
the universe's combined bars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from statistics import mean

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv


@dataclass
class UptrendPoint:
    day: date
    ratio: float                    # 0-100
    eligible: int
    above_200sma: int


@dataclass
class UptrendResult:
    as_of: date
    current_ratio: float
    eligible_today: int
    regime: str
    history: list[UptrendPoint] = field(default_factory=list)
    divergence_detected: bool = False
    divergence_note: str = ""


def _sma(closes: list[float], window: int) -> float | None:
    if len(closes) < window:
        return None
    return mean(closes[-window:])


def _classify_regime(ratio: float) -> str:
    if ratio >= 70.0:
        return "STRONG_UPTREND"
    if ratio >= 50.0:
        return "UPTREND"
    if ratio >= 30.0:
        return "NEUTRAL"
    return "DOWNTREND"


def compute_uptrend_ratio_at(
    bars_by_symbol: dict[str, list[Ohlcv]],
    *,
    at_index: int,
    min_history: int = 200,
) -> tuple[int, int]:
    """Return (eligible_count, above_200sma_count) at `at_index` across symbols.

    Each symbol's bars list is treated as chronological; we slice
    `[:at_index + 1]` and compute the trailing 200-SMA. Names with fewer
    than `min_history` bars at this point are excluded.
    """
    eligible = above = 0
    for _, bars in bars_by_symbol.items():
        if at_index >= len(bars):
            continue
        window = bars[: at_index + 1]
        if len(window) < min_history:
            continue
        sma200 = _sma([b.close for b in window], 200)
        if sma200 is None:
            continue
        eligible += 1
        if window[-1].close > sma200:
            above += 1
    return eligible, above


def compute_uptrend_series(
    bars_by_symbol: dict[str, list[Ohlcv]],
    *,
    history_days: int = 252,
    min_history: int = 200,
) -> list[UptrendPoint]:
    """Compute the historical uptrend ratio over the last `history_days`.

    Uses the union of every symbol's date list to define the timeline,
    then evaluates the ratio at each timeline date.
    """
    all_days: set[date] = set()
    for bars in bars_by_symbol.values():
        all_days.update(b.day for b in bars)
    timeline = sorted(all_days)[-history_days:]

    # Index each symbol's bars by date for fast lookup
    bars_by_day: dict[str, dict[date, list[Ohlcv]]] = {}
    for sym, bars in bars_by_symbol.items():
        s = sorted(bars, key=lambda b: b.day)
        bars_by_day[sym] = s  # keep as list; we slice with bisect

    out: list[UptrendPoint] = []
    for day in timeline:
        eligible = above = 0
        for sym, bars in bars_by_day.items():
            window = [b for b in bars if b.day <= day]
            if len(window) < min_history:
                continue
            sma200 = _sma([b.close for b in window], 200)
            if sma200 is None:
                continue
            eligible += 1
            if window[-1].close > sma200:
                above += 1
        ratio = (above / eligible * 100.0) if eligible else 0.0
        out.append(UptrendPoint(day=day, ratio=round(ratio, 1), eligible=eligible, above_200sma=above))
    return out


def detect_divergence(
    series: list[UptrendPoint],
    *,
    index_series: list[Ohlcv] | None,
    lookback: int = 30,
) -> tuple[bool, str]:
    """Detect classic bearish divergence: index new high while ratio falls.

    Returns (flag, human-readable note).
    """
    if not series or index_series is None or len(index_series) < lookback:
        return False, "insufficient data for divergence check"
    # Align series and index by date
    index_by_day = {b.day: b for b in index_series}
    recent = series[-lookback:]
    pairs = [(p, index_by_day.get(p.day)) for p in recent if p.day in index_by_day]
    if len(pairs) < 5:
        return False, "insufficient overlap between ratio and index series"
    # Index high in window
    idx_high_at = max(pairs, key=lambda p: p[1].close)
    idx_high_close = idx_high_at[1].close
    cur_close = pairs[-1][1].close
    cur_ratio = pairs[-1][0].ratio
    high_ratio = idx_high_at[0].ratio
    # Bearish divergence: index near its lookback high but ratio well below
    if cur_close >= idx_high_close * 0.99 and cur_ratio < high_ratio - 5.0:
        return True, (
            f"index near {lookback}-day high ({cur_close:.0f}) but uptrend ratio "
            f"{cur_ratio:.0f}% is {high_ratio - cur_ratio:.0f}pp below its peak — "
            "bearish breadth divergence"
        )
    return False, "no divergence"


def build_result(
    bars_by_symbol: dict[str, list[Ohlcv]],
    *,
    today: date,
    index_series: list[Ohlcv] | None = None,
    history_days: int = 252,
) -> UptrendResult:
    """Top-level convenience: compute current ratio + history + divergence."""
    series = compute_uptrend_series(bars_by_symbol, history_days=history_days)
    if not series:
        return UptrendResult(
            as_of=today, current_ratio=0.0, eligible_today=0,
            regime="UNKNOWN", history=[], divergence_detected=False,
            divergence_note="no series computed",
        )
    last = series[-1]
    flag, note = detect_divergence(series, index_series=index_series)
    return UptrendResult(
        as_of=today,
        current_ratio=last.ratio,
        eligible_today=last.eligible,
        regime=_classify_regime(last.ratio),
        history=series,
        divergence_detected=flag,
        divergence_note=note,
    )
