"""Pure-functional NEPSE breadth indicator math.

No I/O, no network. Tests inject synthetic OHLCV.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv, Security


@dataclass
class BreadthInputs:
    """OHLCV bundle for one symbol — at least `new_high_lookback` bars."""

    security: Security
    bars: list[Ohlcv]   # chronological order; last bar is the as-of session


@dataclass
class BreadthResult:
    as_of: str
    total_universe: int
    eligible: int                # how many had enough history to score
    advances: int
    declines: int
    unchanged: int
    new_52w_highs: int
    new_52w_lows: int
    pct_above_50sma: float
    pct_above_200sma: float
    ad_ratio: float
    sector_breakdown: dict[str, dict] = field(default_factory=dict)
    regime: str = "UNKNOWN"


def _sma(bars: list[Ohlcv], window: int) -> float | None:
    if len(bars) < window:
        return None
    return mean(b.close for b in bars[-window:])


def _classify_regime(pct_above_200sma: float, pct_above_50sma: float, ad_ratio: float) -> str:
    """Coarse regime label.

    BULL_BROAD : >= 60% above 50-SMA and >= 55% above 200-SMA
    BULL_NARROW: >= 55% above 200-SMA but < 60% above 50-SMA
    NEUTRAL    : between bull and bear thresholds
    BEAR_NARROW: < 40% above 200-SMA and ad_ratio still > 0.7
    BEAR_BROAD : < 40% above 200-SMA and ad_ratio < 0.7
    """
    if pct_above_200sma >= 55.0 and pct_above_50sma >= 60.0:
        return "BULL_BROAD"
    if pct_above_200sma >= 55.0:
        return "BULL_NARROW"
    if pct_above_200sma < 40.0:
        return "BEAR_BROAD" if ad_ratio < 0.7 else "BEAR_NARROW"
    return "NEUTRAL"


def compute_breadth(
    inputs: list[BreadthInputs],
    *,
    as_of: str,
    new_high_lookback: int = 252,
    min_trading_days: int = 150,
) -> BreadthResult:
    """Aggregate breadth indicators across the NEPSE universe."""
    total = len(inputs)
    if total == 0:
        return BreadthResult(
            as_of=as_of, total_universe=0, eligible=0,
            advances=0, declines=0, unchanged=0,
            new_52w_highs=0, new_52w_lows=0,
            pct_above_50sma=0.0, pct_above_200sma=0.0,
            ad_ratio=0.0, sector_breakdown={}, regime="UNKNOWN",
        )

    eligible = 0
    advances = declines = unchanged = 0
    new_highs = new_lows = 0
    above_50 = above_200 = 0
    sector_stats: dict[str, dict[str, int]] = {}

    for bundle in inputs:
        bars = bundle.bars
        if len(bars) < min_trading_days:
            continue
        eligible += 1

        last, prev = bars[-1], bars[-2] if len(bars) >= 2 else bars[-1]
        sec_id = bundle.security.sector_id
        ssec = sector_stats.setdefault(
            sec_id, {"advances": 0, "declines": 0, "unchanged": 0, "eligible": 0}
        )
        ssec["eligible"] += 1

        if last.close > prev.close:
            advances += 1
            ssec["advances"] += 1
        elif last.close < prev.close:
            declines += 1
            ssec["declines"] += 1
        else:
            unchanged += 1
            ssec["unchanged"] += 1

        # 52-week new high/low — slice the most recent `new_high_lookback` bars
        window = bars[-new_high_lookback:]
        window_high = max(b.high for b in window)
        window_low = min(b.low for b in window)
        if last.high >= window_high:
            new_highs += 1
        if last.low <= window_low:
            new_lows += 1

        sma50 = _sma(bars, 50)
        sma200 = _sma(bars, 200)
        if sma50 is not None and last.close > sma50:
            above_50 += 1
        if sma200 is not None and last.close > sma200:
            above_200 += 1

    pct_50 = (above_50 / eligible * 100.0) if eligible else 0.0
    pct_200 = (above_200 / eligible * 100.0) if eligible else 0.0
    ad_ratio = (advances / declines) if declines else float("inf") if advances else 0.0
    if ad_ratio == float("inf"):
        ad_ratio = 999.0

    return BreadthResult(
        as_of=as_of,
        total_universe=total,
        eligible=eligible,
        advances=advances,
        declines=declines,
        unchanged=unchanged,
        new_52w_highs=new_highs,
        new_52w_lows=new_lows,
        pct_above_50sma=round(pct_50, 1),
        pct_above_200sma=round(pct_200, 1),
        ad_ratio=round(ad_ratio, 2),
        sector_breakdown=sector_stats,
        regime=_classify_regime(pct_200, pct_50, ad_ratio),
    )
