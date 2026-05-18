"""Pure-functional distribution day detection on a single index series."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv


@dataclass
class DistributionDay:
    day: date
    close: float
    prev_close: float
    pct_change: float          # negative (it's a down day)
    volume: int
    prev_volume: int
    volume_ratio: float        # vol / prev_vol
    cancelled: bool = False    # True if a subsequent +5% rally absorbed it


@dataclass
class DistributionResult:
    as_of: date
    window: int
    min_down_pct: float
    rally_cancel_pct: float
    distribution_days: list[DistributionDay]
    active_count: int          # not cancelled, within window
    severity: str              # HEALTHY / CAUTION / RISK / DISTRIBUTION


def detect_distribution_days(
    bars: list[Ohlcv],
    *,
    window: int = 25,
    min_down_pct: float = 0.2,
    rally_cancel_pct: float = 5.0,
) -> DistributionResult:
    """Find IBD-style distribution days in the last `window` sessions.

    A distribution day:
      - index closes down ≥ `min_down_pct`% vs previous session
      - volume > previous session's volume

    A distribution day is CANCELLED if a subsequent session within the window
    closes ≥ `rally_cancel_pct`% above the distribution-day's close.
    """
    if not bars:
        return DistributionResult(
            as_of=date.today(), window=window, min_down_pct=min_down_pct,
            rally_cancel_pct=rally_cancel_pct, distribution_days=[],
            active_count=0, severity="UNKNOWN",
        )
    bars = sorted(bars, key=lambda b: b.day)
    if len(bars) < window + 1:
        return DistributionResult(
            as_of=bars[-1].day, window=window, min_down_pct=min_down_pct,
            rally_cancel_pct=rally_cancel_pct, distribution_days=[],
            active_count=0, severity="UNKNOWN",
        )

    recent = bars[-window:]
    recent_with_prev = [(recent[i - 1] if i > 0 else bars[-window - 1], recent[i])
                        for i in range(len(recent))]
    candidates: list[DistributionDay] = []
    for prev, today in recent_with_prev:
        if prev.close <= 0:
            continue
        pct = (today.close - prev.close) / prev.close * 100.0
        if pct > -min_down_pct:
            continue
        if today.volume <= prev.volume:
            continue
        candidates.append(
            DistributionDay(
                day=today.day,
                close=round(today.close, 2),
                prev_close=round(prev.close, 2),
                pct_change=round(pct, 2),
                volume=today.volume,
                prev_volume=prev.volume,
                volume_ratio=round(today.volume / max(prev.volume, 1), 2),
            )
        )

    # Apply cancellation: if a later bar (within the window) closes ≥ rally_cancel_pct above the d-day's close
    for d in candidates:
        for b in recent:
            if b.day <= d.day:
                continue
            if b.close >= d.close * (1.0 + rally_cancel_pct / 100.0):
                d.cancelled = True
                break

    active = sum(1 for d in candidates if not d.cancelled)
    severity = _classify_severity(active)
    return DistributionResult(
        as_of=recent[-1].day,
        window=window,
        min_down_pct=min_down_pct,
        rally_cancel_pct=rally_cancel_pct,
        distribution_days=candidates,
        active_count=active,
        severity=severity,
    )


def _classify_severity(active: int) -> str:
    if active <= 2:
        return "HEALTHY"
    if active == 3:
        return "CAUTION"
    if active == 4:
        return "RISK"
    return "DISTRIBUTION"
