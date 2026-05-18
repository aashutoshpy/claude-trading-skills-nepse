"""Pure-functional NEPSE Kanchi dividend quality scoring.

Takes nepse-value-dividend-screener candidate dicts and scores them
for Kanchi-style entry quality. No I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

import _path_setup  # noqa: F401


@dataclass
class KanchiScore:
    symbol: str
    sector: str
    score: int                    # 0-100
    verdict: str                  # PASS / WATCH / SKIP
    yield_pct: float
    cash_bonus_ratio: float | None
    distance_to_sma200_pct: float | None
    notes: list[str]


def score_candidate(candidate: dict) -> KanchiScore:
    """Apply Kanchi-style quality checks to one nepse-value-dividend-screener row."""
    sym = str(candidate.get("symbol") or "").upper()
    sector = str(candidate.get("sector") or "")
    yield_pct = float(candidate.get("yield_pct") or 0)
    cash = float(candidate.get("cash_div_pct") or 0)
    bonus = float(candidate.get("bonus_div_pct") or 0)
    dist_sma200 = candidate.get("distance_to_sma200_pct")
    if dist_sma200 is not None:
        dist_sma200 = float(dist_sma200)
    notes: list[str] = []
    score = 0

    # Factor 1 — yield magnitude (0-30 pts)
    if yield_pct >= 10:
        score += 30
        notes.append(f"yield {yield_pct}% is high")
    elif yield_pct >= 7:
        score += 25
    elif yield_pct >= 5:
        score += 18
    else:
        score += 5
        notes.append(f"yield {yield_pct}% below 5% — borderline for Kanchi style")

    # Factor 2 — cash-vs-bonus split (0-25 pts)
    total = cash + bonus
    cash_bonus_ratio = round(cash / total, 2) if total > 0 else None
    if cash_bonus_ratio is None:
        notes.append("no dividend split data")
        # neutral 12 pts
        score += 12
    elif cash_bonus_ratio >= 0.7:
        score += 25
        notes.append(f"cash-heavy ({cash_bonus_ratio:.0%} cash) — preferred for income")
    elif cash_bonus_ratio >= 0.4:
        score += 18
    else:
        score += 8
        notes.append(f"bonus-heavy ({(1 - cash_bonus_ratio):.0%} bonus) — dilutive, accept only if sector-typical")

    # Factor 3 — entry quality vs SMA200 (0-25 pts)
    if dist_sma200 is None:
        score += 12
        notes.append("no SMA200 distance")
    elif dist_sma200 <= -10:
        score += 25
        notes.append(f"price {abs(dist_sma200):.0f}% below SMA200 — value zone")
    elif dist_sma200 <= 0:
        score += 22
        notes.append("price slightly below SMA200 — good entry")
    elif dist_sma200 <= 10:
        score += 15
        notes.append("price near SMA200")
    else:
        score += 5
        notes.append(f"price {dist_sma200:.0f}% above SMA200 — wait for pullback")

    # Factor 4 — sector quality (0-20 pts)
    preferred_sectors = {"BANKING", "LIFE_INSURANCE", "NON_LIFE_INSURANCE"}
    cautious_sectors = {"MICROFINANCE", "DEVELOPMENT_BANK", "FINANCE"}
    if sector in preferred_sectors:
        score += 20
        notes.append(f"{sector} — preferred for Kanchi income")
    elif sector in cautious_sectors:
        score += 12
        notes.append(f"{sector} — accept with caution (dividend volatility)")
    else:
        score += 5
        notes.append(f"{sector} — non-traditional dividend sector")

    verdict = _classify(score)
    return KanchiScore(
        symbol=sym, sector=sector, score=score, verdict=verdict,
        yield_pct=yield_pct, cash_bonus_ratio=cash_bonus_ratio,
        distance_to_sma200_pct=dist_sma200, notes=notes,
    )


def _classify(score: int) -> str:
    if score >= 75:
        return "PASS"
    if score >= 55:
        return "WATCH"
    return "SKIP"


def score_candidates(candidates: list[dict]) -> list[KanchiScore]:
    rows = [score_candidate(c) for c in candidates]
    rows.sort(key=lambda r: r.score, reverse=True)
    return rows
