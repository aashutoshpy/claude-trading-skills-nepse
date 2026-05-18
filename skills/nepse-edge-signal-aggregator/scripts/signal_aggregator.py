"""Pure-functional NEPSE edge signal aggregator.

Inputs: list of parsed edge-ticket dicts + optional sector ranking.
Outputs: prioritized signal list. No I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import _path_setup  # noqa: F401

DETECTOR_CONFIDENCE = {
    "circuit_day_continuation": 80,
    "monsoon_hydro_cluster":    70,
    "microfinance_turnaround":  60,
    "bfi_dividend_pullback":    65,
}


@dataclass
class Signal:
    symbol: str
    sector: str
    composite_score: int
    status: str                     # ACT / WATCH / NOISE
    confluence: int
    detectors_flagged: list[str]
    recency_score: int
    detector_confidence: int
    sector_boost: int
    ticket_refs: list[str] = field(default_factory=list)


def _recency_score(ticket_date: date | None, today: date, max_age_days: int) -> int:
    if ticket_date is None:
        return 50
    age = (today - ticket_date).days
    if age <= 0:
        return 100
    if age >= max_age_days:
        return 0
    return int(round((1.0 - age / max_age_days) * 100))


def _classify_status(score: int) -> str:
    if score >= 75:
        return "ACT"
    if score >= 50:
        return "WATCH"
    return "NOISE"


def _sector_boost(sector: str, leading_sectors: list[str]) -> int:
    if not leading_sectors:
        return 10   # neutral when we have no sector data
    return 20 if sector in leading_sectors else 0


def aggregate(
    tickets: list[dict],
    *,
    today: date,
    max_age_days: int = 7,
    leading_sectors: list[str] | None = None,
) -> list[Signal]:
    """Aggregate edge tickets into ranked signals.

    Each `ticket` is the dict shape produced by `nepse-edge-candidate-agent`:
        {ticket_id, detector, as_of, candidates: [{symbol, sector, ...}, ...], ...}
    """
    leading = leading_sectors or []
    # Symbol → list of (detector, sector, ticket_date, ticket_id)
    by_symbol: dict[str, list[tuple]] = {}
    for t in tickets:
        det = t.get("detector") or "unknown"
        ticket_id = t.get("ticket_id") or "?"
        try:
            ticket_date = date.fromisoformat(str(t.get("as_of")))
        except (ValueError, TypeError):
            ticket_date = None
        for cand in t.get("candidates") or []:
            sym = (cand.get("symbol") or "").upper()
            if not sym:
                continue
            sec = cand.get("sector") or "OTHERS"
            by_symbol.setdefault(sym, []).append((det, sec, ticket_date, ticket_id))

    signals: list[Signal] = []
    for sym, hits in by_symbol.items():
        # Filter out stale hits
        fresh = [
            h for h in hits
            if h[2] is None or (today - h[2]).days <= max_age_days
        ]
        if not fresh:
            continue
        detectors = sorted({h[0] for h in fresh})
        confluence = len(detectors)
        # Sector and recency taken from the freshest hit
        fresh_sorted = sorted(fresh, key=lambda h: h[2] or date.min, reverse=True)
        sector = fresh_sorted[0][1]
        most_recent_date = fresh_sorted[0][2]
        recency = _recency_score(most_recent_date, today, max_age_days)
        detector_confidence = max(DETECTOR_CONFIDENCE.get(d, 50) for d in detectors)
        sec_boost = _sector_boost(sector, leading)
        score = int(round(
            confluence * 30 / max(1, len(DETECTOR_CONFIDENCE))   # confluence normalized
            + recency * 0.25
            + detector_confidence * 0.25
            + sec_boost
        ))
        # Cap to 0-100
        score = max(0, min(100, score))
        signals.append(Signal(
            symbol=sym,
            sector=sector,
            composite_score=score,
            status=_classify_status(score),
            confluence=confluence,
            detectors_flagged=detectors,
            recency_score=recency,
            detector_confidence=detector_confidence,
            sector_boost=sec_boost,
            ticket_refs=[h[3] for h in fresh_sorted],
        ))
    signals.sort(key=lambda s: s.composite_score, reverse=True)
    return signals
