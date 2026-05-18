"""Pure-functional NEPSE downtrend detection.

Walks a chronological index series, identifies peak→trough drawdowns
that meet a minimum depth threshold, and tracks recovery dates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import median

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv


@dataclass
class Drawdown:
    peak_date: date
    peak_close: float
    trough_date: date
    trough_close: float
    depth_pct: float                 # negative
    decline_days: int                # trading days from peak to trough
    recovery_date: date | None = None
    recovery_days: int | None = None
    total_days: int | None = None


@dataclass
class DowntrendSummary:
    drawdowns: list[Drawdown]
    in_progress: Drawdown | None
    decline_days_p25: int | None
    decline_days_median: int | None
    decline_days_p75: int | None
    decline_days_max: int | None
    recovery_days_p25: int | None
    recovery_days_median: int | None
    recovery_days_p75: int | None
    recovery_days_max: int | None
    historical_count: int


def _percentile(sorted_vals: list[int], pct: float) -> int | None:
    if not sorted_vals:
        return None
    idx = max(0, min(len(sorted_vals) - 1, int(round(pct / 100 * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def detect_drawdowns(
    bars: list[Ohlcv],
    *,
    min_depth_pct: float = 10.0,
) -> list[Drawdown]:
    """Walk the series forward, tracking running peak and recording drawdowns
    that breach `min_depth_pct` from peak to trough.

    A drawdown ends when the index recovers to its prior peak.
    """
    if not bars:
        return []
    bars = sorted(bars, key=lambda b: b.day)
    drawdowns: list[Drawdown] = []

    running_peak = bars[0].close
    running_peak_day = bars[0].day
    running_peak_idx = 0
    candidate: Drawdown | None = None

    for i, bar in enumerate(bars):
        if bar.close > running_peak:
            # New all-time-high (within window). If we were tracking a
            # candidate drawdown, this point recovers it.
            if candidate is not None:
                candidate.recovery_date = bar.day
                candidate.recovery_days = i - _index_of_day(bars, candidate.trough_date)
                candidate.total_days = candidate.decline_days + (candidate.recovery_days or 0)
                drawdowns.append(candidate)
                candidate = None
            running_peak = bar.close
            running_peak_day = bar.day
            running_peak_idx = i
            continue

        # Decline / drawdown: check if it qualifies
        depth = (bar.close - running_peak) / running_peak * 100.0
        if depth <= -min_depth_pct:
            if candidate is None:
                candidate = Drawdown(
                    peak_date=running_peak_day,
                    peak_close=running_peak,
                    trough_date=bar.day,
                    trough_close=bar.close,
                    depth_pct=round(depth, 2),
                    decline_days=i - running_peak_idx,
                )
            elif bar.close < candidate.trough_close:
                # New low within this drawdown
                candidate.trough_date = bar.day
                candidate.trough_close = bar.close
                candidate.depth_pct = round(depth, 2)
                candidate.decline_days = i - running_peak_idx

    # If a drawdown is still in progress (no recovery), keep it but mark as in-progress
    if candidate is not None:
        drawdowns.append(candidate)
    return drawdowns


def _index_of_day(bars: list[Ohlcv], target: date) -> int:
    for i, b in enumerate(bars):
        if b.day == target:
            return i
    return -1


def summarize(drawdowns: list[Drawdown]) -> DowntrendSummary:
    completed = [d for d in drawdowns if d.recovery_date is not None]
    in_progress = next((d for d in drawdowns if d.recovery_date is None), None)

    declines = sorted(d.decline_days for d in completed)
    recoveries = sorted(d.recovery_days for d in completed if d.recovery_days is not None)

    return DowntrendSummary(
        drawdowns=drawdowns,
        in_progress=in_progress,
        decline_days_p25=_percentile(declines, 25),
        decline_days_median=int(median(declines)) if declines else None,
        decline_days_p75=_percentile(declines, 75),
        decline_days_max=max(declines) if declines else None,
        recovery_days_p25=_percentile(recoveries, 25),
        recovery_days_median=int(median(recoveries)) if recoveries else None,
        recovery_days_p75=_percentile(recoveries, 75),
        recovery_days_max=max(recoveries) if recoveries else None,
        historical_count=len(completed),
    )
