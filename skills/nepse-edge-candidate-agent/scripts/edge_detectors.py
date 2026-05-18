"""Pure-functional NEPSE edge anomaly detectors.

Each detector takes a `symbol -> bars` map (chronological) plus optional
context, and returns a list of EdgeObservation dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv, Security


@dataclass
class EdgeObservation:
    symbol: str
    sector: str
    observation: dict


CIRCUIT_GAIN_PCT = 14.5     # near-upper-circuit (15% band, post-April 2026)
CIRCUIT_VOL_RATIO_MIN = 2.0
RECENT_SESSIONS = 5


def _avg_volume(bars: list[Ohlcv], n: int) -> float:
    if len(bars) < n:
        return 0.0
    return mean(b.volume for b in bars[-n:])


# ---- circuit_day_continuation -----------------------------------------


def detect_circuit_day_continuation(
    bars_by_symbol: dict[str, list[Ohlcv]],
    securities_by_symbol: dict[str, Security],
) -> list[EdgeObservation]:
    out: list[EdgeObservation] = []
    for sym, bars in bars_by_symbol.items():
        if len(bars) < 30:
            continue
        sorted_bars = sorted(bars, key=lambda b: b.day)
        avg = _avg_volume(sorted_bars[:-RECENT_SESSIONS], 20)
        if avg <= 0:
            continue
        for i in range(max(0, len(sorted_bars) - RECENT_SESSIONS), len(sorted_bars)):
            bar = sorted_bars[i]
            prev_close = sorted_bars[i - 1].close if i > 0 else bar.open
            if prev_close <= 0:
                continue
            gain_pct = (bar.close - prev_close) / prev_close * 100.0
            if gain_pct < CIRCUIT_GAIN_PCT:
                continue
            vol_ratio = bar.volume / avg if avg > 0 else 0
            if vol_ratio < CIRCUIT_VOL_RATIO_MIN:
                continue
            sec = securities_by_symbol.get(sym)
            out.append(EdgeObservation(
                symbol=sym,
                sector=sec.sector_id if sec else "OTHERS",
                observation={
                    "circuit_date": bar.day.isoformat(),
                    "circuit_close": round(bar.close, 2),
                    "gain_pct": round(gain_pct, 2),
                    "volume_ratio": round(vol_ratio, 2),
                },
            ))
            break  # one observation per symbol
    return out


# ---- monsoon_hydro_cluster --------------------------------------------


def detect_monsoon_hydro_cluster(
    bars_by_symbol: dict[str, list[Ohlcv]],
    securities_by_symbol: dict[str, Security],
    *,
    today: date,
) -> list[EdgeObservation]:
    # Monsoon window: May (month=5) through August (month=8)
    if today.month < 5 or today.month > 8:
        return []
    out: list[EdgeObservation] = []
    for sym, bars in bars_by_symbol.items():
        sec = securities_by_symbol.get(sym)
        if not sec or sec.sector_id != "HYDROPOWER":
            continue
        if len(bars) < 35:
            continue
        sorted_bars = sorted(bars, key=lambda b: b.day)
        window = sorted_bars[-30:]
        last = sorted_bars[-1]
        window_high = max(b.high for b in window[:-1])
        if last.high >= window_high * 0.999:
            out.append(EdgeObservation(
                symbol=sym,
                sector="HYDROPOWER",
                observation={
                    "new_30d_high_date": last.day.isoformat(),
                    "new_30d_high": round(last.high, 2),
                    "prior_high": round(window_high, 2),
                },
            ))
    return out


# ---- microfinance_turnaround ------------------------------------------


def detect_microfinance_turnaround(
    bars_by_symbol: dict[str, list[Ohlcv]],
    securities_by_symbol: dict[str, Security],
) -> list[EdgeObservation]:
    out: list[EdgeObservation] = []
    for sym, bars in bars_by_symbol.items():
        sec = securities_by_symbol.get(sym)
        if not sec or sec.sector_id != "MICROFINANCE":
            continue
        if len(bars) < 95:
            continue
        sorted_bars = sorted(bars, key=lambda b: b.day)
        window_90 = sorted_bars[-95:-5]
        if not window_90:
            continue
        ninety_day_low = min(b.low for b in window_90)
        last = sorted_bars[-1]
        if ninety_day_low <= 0:
            continue
        bounce_pct = (last.close - ninety_day_low) / ninety_day_low * 100.0
        # Bounce must have happened within last 5 sessions
        recent_low = min(b.low for b in sorted_bars[-5:])
        if recent_low > ninety_day_low * 1.05:
            continue
        if bounce_pct < 10.0:
            continue
        out.append(EdgeObservation(
            symbol=sym,
            sector="MICROFINANCE",
            observation={
                "ninety_day_low": round(ninety_day_low, 2),
                "current_close": round(last.close, 2),
                "bounce_pct": round(bounce_pct, 2),
            },
        ))
    return out


# ---- bfi_dividend_pullback -------------------------------------------


def detect_bfi_dividend_pullback(
    bars_by_symbol: dict[str, list[Ohlcv]],
    securities_by_symbol: dict[str, Security],
    *,
    dividend_records: dict[str, dict] | None = None,
) -> list[EdgeObservation]:
    """Detect BFI names that gapped down roughly by their dividend amount.

    Without dividend_records, falls back to flagging any BFI gap-down 8-15% in
    the last 10 sessions (heuristic only).
    """
    out: list[EdgeObservation] = []
    bfi_sectors = {"BANKING", "DEVELOPMENT_BANK", "FINANCE", "LIFE_INSURANCE", "NON_LIFE_INSURANCE"}
    for sym, bars in bars_by_symbol.items():
        sec = securities_by_symbol.get(sym)
        if not sec or sec.sector_id not in bfi_sectors:
            continue
        if len(bars) < 12:
            continue
        sorted_bars = sorted(bars, key=lambda b: b.day)
        for i in range(max(1, len(sorted_bars) - 10), len(sorted_bars)):
            prev_close = sorted_bars[i - 1].close
            bar = sorted_bars[i]
            if prev_close <= 0:
                continue
            gap_pct = (bar.open - prev_close) / prev_close * 100.0
            if not (-15.0 <= gap_pct <= -8.0):
                continue
            # Match dividend amount if records are supplied
            note = "no dividend record available — heuristic flag only"
            if dividend_records and sym in dividend_records:
                rec = dividend_records[sym]
                expected_pct = -(float(rec.get("cash_div_pct", 0)) + float(rec.get("bonus_div_pct", 0))) / 100.0 * (100.0 / max(prev_close, 1))
                note = f"dividend ~{expected_pct:.1f}%; observed gap {gap_pct:.1f}%"
            out.append(EdgeObservation(
                symbol=sym,
                sector=sec.sector_id,
                observation={
                    "gap_date": bar.day.isoformat(),
                    "gap_pct": round(gap_pct, 2),
                    "prev_close": round(prev_close, 2),
                    "open_after_gap": round(bar.open, 2),
                    "note": note,
                },
            ))
            break  # one per symbol
    return out
