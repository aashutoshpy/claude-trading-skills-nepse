"""Pure-functional NEPSE post-result 5-factor scoring.

Inputs: chronological OHLCV + a report-date. Output: a structured
score dict. No I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from statistics import mean

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv

WEIGHTS = {
    "gap": 0.20,
    "trend": 0.25,
    "volume": 0.20,
    "ma200": 0.15,
    "ma50": 0.20,
}


@dataclass
class EarningsScore:
    symbol: str
    report_date: date
    reaction_date: date | None
    rating: str
    score: int
    gap_pct: float | None
    trend_stage: str
    volume_surge: float | None        # ratio to 20-day avg
    distance_to_ma200_pct: float | None
    distance_to_ma50_pct: float | None
    components: dict[str, dict] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _sma(closes: list[float], window: int) -> float | None:
    if len(closes) < window:
        return None
    return mean(closes[-window:])


def _classify_stage(bars: list[Ohlcv]) -> str:
    if len(bars) < 200:
        return "UNKNOWN"
    sma50 = _sma([b.close for b in bars], 50)
    sma200 = _sma([b.close for b in bars], 200)
    sma200_past = _sma([b.close for b in bars[:-20]], 200) if len(bars) >= 220 else None
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


def _classify_rating(score: int) -> str:
    if score >= 80:
        return "STRONG_CONTINUATION"
    if score >= 60:
        return "CONTINUATION"
    if score >= 40:
        return "NEUTRAL"
    if score >= 20:
        return "FADE_RISK"
    return "STRONG_FADE_RISK"


def score_earnings(
    bars: list[Ohlcv],
    *,
    symbol: str,
    report_date: date,
) -> EarningsScore:
    """5-factor score for a NEPSE post-result reaction."""
    bars = sorted(bars, key=lambda b: b.day)
    if len(bars) < 200:
        return EarningsScore(
            symbol=symbol, report_date=report_date, reaction_date=None,
            rating="UNKNOWN", score=0, gap_pct=None, trend_stage="UNKNOWN",
            volume_surge=None, distance_to_ma200_pct=None, distance_to_ma50_pct=None,
            notes=["insufficient history (<200 bars)"],
        )

    # Reaction = first trading day at or after report_date
    reaction_idx = next((i for i, b in enumerate(bars) if b.day >= report_date), None)
    if reaction_idx is None or reaction_idx == 0:
        return EarningsScore(
            symbol=symbol, report_date=report_date, reaction_date=None,
            rating="UNKNOWN", score=0, gap_pct=None, trend_stage="UNKNOWN",
            volume_surge=None, distance_to_ma200_pct=None, distance_to_ma50_pct=None,
            notes=["no post-report bar in series"],
        )
    reaction_bar = bars[reaction_idx]
    prev_bar = bars[reaction_idx - 1]
    history = bars[:reaction_idx + 1]   # include the reaction bar
    closes = [b.close for b in history]

    # --- factor: gap %
    gap_pct = round((reaction_bar.open - prev_bar.close) / prev_bar.close * 100.0, 2)
    if abs(gap_pct) >= 10.0:
        gap_score = 100 if gap_pct > 0 else 0
    elif abs(gap_pct) >= 4.0:
        gap_score = 75 if gap_pct > 0 else 25
    else:
        gap_score = 50

    # --- factor: trend stage
    stage = _classify_stage(history[:-1])   # stage as of pre-reaction
    trend_score = {"STAGE_2": 90, "STAGE_1": 55, "STAGE_3": 35, "STAGE_4": 10}.get(stage, 50)

    # --- factor: volume surge
    if reaction_idx >= 20:
        vol_window = [b.volume for b in bars[reaction_idx - 20: reaction_idx]]
        avg20 = mean(vol_window) if vol_window else 0
        vol_ratio = reaction_bar.volume / avg20 if avg20 > 0 else 0.0
    else:
        vol_ratio = 0.0
    if vol_ratio >= 1.8:
        volume_score = 90
    elif vol_ratio >= 1.2:
        volume_score = 65
    elif vol_ratio >= 0.8:
        volume_score = 45
    else:
        volume_score = 20

    # --- factor: distance to MA200
    sma200 = _sma(closes, 200)
    dist_200 = None
    if sma200 and sma200 > 0:
        dist_200 = round((reaction_bar.close - sma200) / sma200 * 100.0, 2)
    if dist_200 is None:
        ma200_score = 50
    elif dist_200 >= 10:
        ma200_score = 90
    elif dist_200 >= 0:
        ma200_score = 65
    elif dist_200 >= -10:
        ma200_score = 30
    else:
        ma200_score = 10

    # --- factor: distance to MA50
    sma50 = _sma(closes, 50)
    dist_50 = None
    if sma50 and sma50 > 0:
        dist_50 = round((reaction_bar.close - sma50) / sma50 * 100.0, 2)
    if dist_50 is None:
        ma50_score = 50
    elif dist_50 >= 5:
        ma50_score = 90
    elif dist_50 >= 0:
        ma50_score = 65
    elif dist_50 >= -5:
        ma50_score = 30
    else:
        ma50_score = 10

    components = {
        "gap":    {"score": gap_score,    "value": gap_pct},
        "trend":  {"score": trend_score,  "value": stage},
        "volume": {"score": volume_score, "value": round(vol_ratio, 2)},
        "ma200":  {"score": ma200_score,  "value": dist_200},
        "ma50":   {"score": ma50_score,   "value": dist_50},
    }
    composite = 0.0
    for key, weight in WEIGHTS.items():
        composite += components[key]["score"] * weight
    score = int(round(composite))

    notes: list[str] = []
    if gap_pct >= 14.5:
        notes.append("gap near +15% upper-circuit limit — true reaction size may be larger than recorded")
    if gap_pct <= -14.5:
        notes.append("gap near -15% lower-circuit limit — true reaction size may be larger than recorded")
    if stage == "STAGE_4":
        notes.append("Stage 4 — even a strong gap is fade-risk in a downtrend")

    return EarningsScore(
        symbol=symbol,
        report_date=report_date,
        reaction_date=reaction_bar.day,
        rating=_classify_rating(score),
        score=score,
        gap_pct=gap_pct,
        trend_stage=stage,
        volume_surge=round(vol_ratio, 2),
        distance_to_ma200_pct=dist_200,
        distance_to_ma50_pct=dist_50,
        components=components,
        notes=notes,
    )
