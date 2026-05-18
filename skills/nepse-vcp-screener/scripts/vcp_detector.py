"""NEPSE VCP pattern detector.

Pure-functional: takes a list of OHLCV bars and returns a structured
analysis. No I/O, no network. Detector logic is intentionally simpler
than the US sibling because NEPSE bases are shorter and the universe
is smaller (~284 names).

Key calibration notes vs. the US sibling:
  - NEPSE moved to a 15% daily band on 2026-04-17 — single-day moves
    that were "limit" in a 10%-band market are now mid-range. The
    `max_final_contraction_pct` default is 6% (vs. 10% in the US).
  - NEPSE EOD volume is sparse; the default `avg_volume_min` is 5,000
    shares (orders of magnitude lower than US S&P 500 names).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

import _path_setup  # noqa: F401 — sys.path setup

from common.nepse.client import Ohlcv


@dataclass
class VcpParameters:
    min_contractions: int = 2
    max_final_contraction_pct: float = 6.0
    min_base_days: int = 15
    avg_volume_min: int = 5_000
    stage2_sma200_rising_days: int = 20
    pivot_distance_max_pct: float = 5.0   # how close to the pivot to flag as actionable


@dataclass
class VcpResult:
    valid_vcp: bool
    base_days: int
    contractions: int
    final_contraction_pct: float | None
    pivot_price: float | None
    distance_to_pivot_pct: float | None
    composite_score: int
    reasons: list[str] = field(default_factory=list)


def _sma(bars: list[Ohlcv], window: int) -> float | None:
    if len(bars) < window:
        return None
    return mean(b.close for b in bars[-window:])


def _is_stage2(bars: list[Ohlcv], params: VcpParameters) -> tuple[bool, str | None]:
    """Stage 2 = price > SMA50 > SMA200; SMA200 rising over the configured window."""
    if len(bars) < 200 + params.stage2_sma200_rising_days:
        return False, "not enough history for SMA200"
    sma50 = _sma(bars, 50)
    sma200 = _sma(bars, 200)
    sma200_then = _sma(bars[:-params.stage2_sma200_rising_days], 200)
    if sma50 is None or sma200 is None or sma200_then is None:
        return False, "SMA computation failed"
    price = bars[-1].close
    if not (price > sma50 > sma200):
        return False, "price/SMA50/SMA200 not in Stage 2 stack"
    if sma200 <= sma200_then:
        return False, "SMA200 not rising"
    return True, None


def _find_swings(bars: list[Ohlcv], lookback: int = 3) -> list[tuple[int, str, float]]:
    """Return [(idx, 'H'|'L', price)] for local pivots in `bars`.

    A bar is a swing-high if its high is the max within ±lookback,
    swing-low if its low is the min within ±lookback. End-of-series
    bars cannot be confirmed and are skipped (we don't know what
    comes after).
    """
    swings: list[tuple[int, str, float]] = []
    for i in range(lookback, len(bars) - lookback):
        window = bars[i - lookback : i + lookback + 1]
        if bars[i].high == max(b.high for b in window):
            swings.append((i, "H", bars[i].high))
        elif bars[i].low == min(b.low for b in window):
            swings.append((i, "L", bars[i].low))
    return swings


def _contractions_from_swings(swings: list[tuple[int, str, float]]) -> list[float]:
    """Each contraction = (swing high - next swing low) / swing high (percent).

    Walks the swing list forward, pairing each H with the L that follows it,
    then reverses the result so the returned list is **most-recent first**.
    The narrowing check downstream relies on this ordering: index 0 is the
    newest leg, index -1 is the oldest.
    """
    contractions: list[float] = []
    i = 0
    while i < len(swings) - 1:
        idx, kind, price = swings[i]
        if kind == "H":
            j = i + 1
            while j < len(swings) and swings[j][1] != "L":
                j += 1
            if j < len(swings):
                low = swings[j][2]
                pct = (price - low) / price * 100.0 if price > 0 else 0.0
                contractions.append(pct)
                i = j + 1
                continue
        i += 1
    contractions.reverse()
    return contractions


def detect_vcp(bars: list[Ohlcv], params: VcpParameters | None = None) -> VcpResult:
    """Run VCP detection on a chronological list of daily OHLCV bars."""
    params = params or VcpParameters()
    if not bars:
        return VcpResult(False, 0, 0, None, None, None, 0, ["no bars"])

    in_stage2, reason = _is_stage2(bars, params)
    if not in_stage2:
        return VcpResult(False, 0, 0, None, None, None, 0, [reason or "not Stage 2"])

    # Restrict pattern detection to the last `min_base_days * 4` bars
    # to keep older noise out — a base older than that has resolved
    # one way or another.
    window = bars[-params.min_base_days * 4 :]

    swings = _find_swings(window)
    swing_highs = [s for s in swings if s[1] == "H"]
    if not swing_highs:
        return VcpResult(False, len(window), 0, None, None, None, 0, ["no swing highs"])

    contractions = _contractions_from_swings(swings)
    if len(contractions) < params.min_contractions:
        return VcpResult(
            False,
            len(window),
            len(contractions),
            contractions[0] if contractions else None,
            None,
            None,
            0,
            [f"only {len(contractions)} contractions (need {params.min_contractions})"],
        )

    # VCP requires the contractions to be *narrowing*: each successive
    # contraction (i.e. moving forward in time) must be tighter than the
    # one before. Because `contractions` is most-recent-first, we check
    # contractions[0] < contractions[1] < ... (each newer one tighter).
    narrowing = all(contractions[i] < contractions[i + 1] for i in range(len(contractions) - 1))
    final_pct = contractions[0]
    pivot_price = swing_highs[0][2]
    distance_to_pivot_pct = (
        (pivot_price - bars[-1].close) / pivot_price * 100.0 if pivot_price > 0 else None
    )

    avg_volume = mean(b.volume for b in window[-20:]) if len(window) >= 20 else 0
    volume_ok = avg_volume >= params.avg_volume_min

    reasons: list[str] = []
    if not narrowing:
        reasons.append("contractions not narrowing")
    if final_pct > params.max_final_contraction_pct:
        reasons.append(
            f"final contraction {final_pct:.1f}% > {params.max_final_contraction_pct}%"
        )
    if not volume_ok:
        reasons.append(f"avg volume {avg_volume:.0f} < {params.avg_volume_min}")

    valid = narrowing and final_pct <= params.max_final_contraction_pct and volume_ok

    score = _composite_score(
        narrowing=narrowing,
        final_pct=final_pct,
        contractions=contractions,
        distance_to_pivot_pct=distance_to_pivot_pct,
        params=params,
    )

    return VcpResult(
        valid_vcp=valid,
        base_days=len(window),
        contractions=len(contractions),
        final_contraction_pct=round(final_pct, 2),
        pivot_price=round(pivot_price, 2),
        distance_to_pivot_pct=round(distance_to_pivot_pct, 2) if distance_to_pivot_pct is not None else None,
        composite_score=score,
        reasons=reasons,
    )


def _composite_score(
    *,
    narrowing: bool,
    final_pct: float,
    contractions: list[float],
    distance_to_pivot_pct: float | None,
    params: VcpParameters,
) -> int:
    """Simple 0-100 composite.

    Weighting:
        - 30 pts: contractions narrowing
        - 30 pts: tighter final contraction (0% → 30, params.max_pct → 0)
        - 20 pts: more contractions (2 → 0, 4+ → 20)
        - 20 pts: closer to pivot (0% → 20, params.pivot_distance_max_pct+ → 0)
    """
    pts = 0.0
    if narrowing:
        pts += 30
    if final_pct <= params.max_final_contraction_pct:
        pts += 30 * (1.0 - final_pct / params.max_final_contraction_pct)
    pts += min(20, max(0, 10 * (len(contractions) - 2)))
    if distance_to_pivot_pct is not None and distance_to_pivot_pct >= 0:
        if distance_to_pivot_pct <= params.pivot_distance_max_pct:
            pts += 20 * (1.0 - distance_to_pivot_pct / params.pivot_distance_max_pct)
    return int(round(pts))
