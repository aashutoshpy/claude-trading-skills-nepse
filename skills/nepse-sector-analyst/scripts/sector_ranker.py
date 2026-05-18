"""Pure-functional sector ranking — return calculation and stage classification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv


@dataclass
class SectorScore:
    sector_id: str
    last_close: float
    returns_pct: dict[str, float]   # window-label → return %
    stage: str                       # "STAGE_2", "STAGE_1", etc.
    ranks: dict[str, int]            # window-label → rank within universe


def _return_over(bars: list[Ohlcv], window: int) -> float | None:
    if len(bars) < window + 1:
        return None
    cur = bars[-1].close
    past = bars[-(window + 1)].close
    if past <= 0:
        return None
    return (cur - past) / past * 100.0


def _ytd_return(bars: list[Ohlcv], today: date) -> float | None:
    year_start = date(today.year, 1, 1)
    candidates = [b for b in bars if b.day >= year_start]
    if not candidates:
        return None
    cur = bars[-1].close
    past = candidates[0].close
    if past <= 0:
        return None
    return (cur - past) / past * 100.0


def _sma(bars: list[Ohlcv], window: int) -> float | None:
    if len(bars) < window:
        return None
    return mean(b.close for b in bars[-window:])


def _classify_stage(bars: list[Ohlcv]) -> str:
    """4-stage classification by SMA stack."""
    if len(bars) < 200:
        return "UNKNOWN"
    sma50 = _sma(bars, 50)
    sma200 = _sma(bars, 200)
    sma200_past = _sma(bars[:-20], 200) if len(bars) >= 220 else None
    if sma50 is None or sma200 is None:
        return "UNKNOWN"
    price = bars[-1].close
    if price > sma50 > sma200 and (sma200_past is None or sma200 > sma200_past):
        return "STAGE_2"
    if price < sma50 < sma200 and (sma200_past is None or sma200 < sma200_past):
        return "STAGE_4"
    if price < sma50 and sma50 > sma200:
        return "STAGE_3"
    return "STAGE_1"


def rank_sectors(
    sector_bars: dict[str, list[Ohlcv]],
    *,
    windows: dict[str, int],
    today: date | None = None,
    include_ytd: bool = True,
) -> list[SectorScore]:
    """Compute scores and ranks per sector.

    `windows` maps a label (e.g. "1w") to a number of trading days (e.g. 5).
    """
    today = today or date.today()
    scores: list[SectorScore] = []
    for sec_id, bars in sector_bars.items():
        if not bars:
            continue
        bars = sorted(bars, key=lambda b: b.day)
        returns: dict[str, float] = {}
        for label, window in windows.items():
            r = _return_over(bars, window)
            if r is not None:
                returns[label] = round(r, 2)
        if include_ytd:
            ytd = _ytd_return(bars, today)
            if ytd is not None:
                returns["ytd"] = round(ytd, 2)
        scores.append(
            SectorScore(
                sector_id=sec_id,
                last_close=round(bars[-1].close, 2),
                returns_pct=returns,
                stage=_classify_stage(bars),
                ranks={},
            )
        )

    # Compute ranks per window
    window_labels = list(windows.keys()) + (["ytd"] if include_ytd else [])
    for label in window_labels:
        ordered = sorted(
            (s for s in scores if label in s.returns_pct),
            key=lambda s: s.returns_pct[label],
            reverse=True,
        )
        for rank, s in enumerate(ordered, start=1):
            s.ranks[label] = rank
    return scores
