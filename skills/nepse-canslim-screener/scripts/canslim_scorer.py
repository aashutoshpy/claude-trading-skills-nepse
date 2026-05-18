"""Pure-functional NEPSE CANSLIM 7-factor scoring.

Inputs: chronological OHLCV per symbol + optional fundamentals dict +
market direction from `nepse-uptrend-analyzer`. No I/O.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from statistics import mean

import _path_setup  # noqa: F401

from common.nepse.client import Ohlcv, Security

WEIGHTS = {
    "C": 0.15,   # Current quarterly EPS growth
    "A": 0.15,   # Annual EPS growth
    "N": 0.15,   # Near 52-week high
    "S": 0.15,   # Supply/demand (volume surge)
    "L": 0.20,   # Leader (relative strength)
    "I": 0.05,   # Institutional sponsorship (partial)
    "M": 0.15,   # Market direction
}


@dataclass
class Fundamentals:
    symbol: str
    eps_latest: float | None = None
    eps_prior_year: float | None = None
    eps_3y_cagr: float | None = None
    sales_3y_cagr: float | None = None

    @property
    def quarterly_eps_growth_pct(self) -> float | None:
        if self.eps_latest is None or self.eps_prior_year is None or self.eps_prior_year == 0:
            return None
        return (self.eps_latest - self.eps_prior_year) / abs(self.eps_prior_year) * 100.0


@dataclass
class CanslimRow:
    symbol: str
    sector: str
    score: int
    rating: str
    components: dict[str, dict] = field(default_factory=dict)
    skipped: bool = False
    skip_reason: str = ""


def parse_fundamentals_csv(text: str) -> dict[str, Fundamentals]:
    out: dict[str, Fundamentals] = {}
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        sym = (row.get("symbol") or "").strip().upper()
        if not sym:
            continue
        out[sym] = Fundamentals(
            symbol=sym,
            eps_latest=_safe_float(row.get("eps_latest")),
            eps_prior_year=_safe_float(row.get("eps_prior_year")),
            eps_3y_cagr=_safe_float(row.get("eps_3y_cagr")),
            sales_3y_cagr=_safe_float(row.get("sales_3y_cagr")),
        )
    return out


def _safe_float(v: str | None) -> float | None:
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _sma(closes: list[float], window: int) -> float | None:
    if len(closes) < window:
        return None
    return mean(closes[-window:])


# ---- factor scorers (each returns 0-100) -------------------------------


def score_C(fund: Fundamentals | None) -> tuple[int, str]:
    if fund is None or fund.quarterly_eps_growth_pct is None:
        return 50, "no fundamentals"
    g = min(fund.quarterly_eps_growth_pct, 100.0)   # cap microfinance outliers
    if g >= 25:
        return 90, f"qtr EPS growth {g:.0f}%"
    if g >= 10:
        return 70, f"qtr EPS growth {g:.0f}%"
    if g >= 0:
        return 40, f"qtr EPS growth {g:.0f}%"
    return 10, f"qtr EPS growth {g:.0f}% (negative)"


def score_A(fund: Fundamentals | None) -> tuple[int, str]:
    if fund is None or fund.eps_3y_cagr is None:
        return 50, "no fundamentals"
    g = min(fund.eps_3y_cagr, 100.0)
    if g >= 25:
        return 90, f"3y EPS CAGR {g:.0f}%"
    if g >= 10:
        return 70, f"3y EPS CAGR {g:.0f}%"
    if g >= 0:
        return 40, f"3y EPS CAGR {g:.0f}%"
    return 10, f"3y EPS CAGR {g:.0f}% (negative)"


def score_N(bars: list[Ohlcv]) -> tuple[int, str]:
    """Near 52-week high — distance to 252-day high."""
    if len(bars) < 252:
        return 30, "insufficient history for 52w high"
    window = bars[-252:]
    high = max(b.high for b in window)
    current = bars[-1].close
    if high <= 0:
        return 30, "invalid high"
    distance = (high - current) / high * 100.0
    if distance <= 3:
        return 90, f"within {distance:.1f}% of 52w high"
    if distance <= 10:
        return 70, f"within {distance:.1f}% of 52w high"
    if distance <= 25:
        return 40, f"{distance:.1f}% below 52w high"
    return 10, f"{distance:.1f}% below 52w high"


def score_S(bars: list[Ohlcv]) -> tuple[int, str]:
    """Volume surge on advance days (last 5 sessions)."""
    if len(bars) < 60:
        return 30, "insufficient history for volume baseline"
    avg_50 = mean(b.volume for b in bars[-55:-5])   # 50-day avg excluding last 5
    if avg_50 <= 0:
        return 30, "avg volume is zero"
    advance_volumes = [b.volume for b in bars[-5:] if b.close > b.open]
    if not advance_volumes:
        return 25, "no advance days in last 5 sessions"
    ratio = max(advance_volumes) / avg_50
    if ratio >= 2.0:
        return 90, f"advance-day volume {ratio:.1f}× avg"
    if ratio >= 1.3:
        return 70, f"advance-day volume {ratio:.1f}× avg"
    return 40, f"advance-day volume {ratio:.1f}× avg"


def score_L(bars: list[Ohlcv], *, index_bars: list[Ohlcv] | None) -> tuple[int, str]:
    """Relative strength vs NEPSE composite — 90-day return."""
    if index_bars is None or len(bars) < 90 or len(index_bars) < 90:
        return 50, "no index data for RS calc"
    sym_ret = (bars[-1].close - bars[-90].close) / max(bars[-90].close, 1) * 100.0
    idx_ret = (index_bars[-1].close - index_bars[-90].close) / max(index_bars[-90].close, 1) * 100.0
    rs = sym_ret - idx_ret
    if rs >= 20:
        return 90, f"RS spread {rs:+.0f}pp"
    if rs >= 10:
        return 75, f"RS spread {rs:+.0f}pp"
    if rs >= 0:
        return 55, f"RS spread {rs:+.0f}pp"
    return 25, f"RS spread {rs:+.0f}pp (lagging)"


def score_I(floorsheet_count: int | None) -> tuple[int, str]:
    """Institutional sponsorship proxy from floorsheet large-trade count."""
    if floorsheet_count is None:
        return 50, "no floorsheet data"
    if floorsheet_count >= 5:
        return 80, f"{floorsheet_count} large trades today"
    if floorsheet_count >= 1:
        return 60, f"{floorsheet_count} large trade(s) today"
    return 40, "no large trades today"


def score_M(uptrend_regime: str | None) -> tuple[int, str]:
    if uptrend_regime is None:
        return 50, "no uptrend data"
    return {
        "STRONG_UPTREND": (95, "strong uptrend"),
        "UPTREND":        (75, "uptrend"),
        "NEUTRAL":        (45, "neutral regime"),
        "DOWNTREND":      (10, "downtrend"),
    }.get(uptrend_regime, (50, f"unknown regime: {uptrend_regime}"))


# ---- aggregator --------------------------------------------------------


def _classify_rating(score: int) -> str:
    if score >= 85:
        return "STRONG_CANSLIM"
    if score >= 70:
        return "CANSLIM"
    if score >= 55:
        return "WATCHLIST"
    return "NO_MATCH"


def score_universe(
    securities: list[Security],
    *,
    bars_by_symbol: dict[str, list[Ohlcv]],
    index_bars: list[Ohlcv] | None,
    fundamentals: dict[str, Fundamentals],
    uptrend_regime: str | None,
    require_strong_uptrend: bool = False,
    max_per_sector: int = 5,
) -> list[CanslimRow]:
    if uptrend_regime == "DOWNTREND" or (require_strong_uptrend and uptrend_regime != "STRONG_UPTREND"):
        return [CanslimRow(
            symbol="(market gate)",
            sector="",
            score=0,
            rating="NO_MATCH",
            skipped=True,
            skip_reason=f"uptrend regime is {uptrend_regime}; no CANSLIM screening attempted",
        )]

    m_score, m_reason = score_M(uptrend_regime)
    rows: list[CanslimRow] = []

    for sec in securities:
        bars = bars_by_symbol.get(sec.symbol.upper())
        if not bars or len(bars) < 90:
            continue
        bars = sorted(bars, key=lambda b: b.day)
        fund = fundamentals.get(sec.symbol.upper())
        components = {
            "C": dict(zip(("score", "reason"), score_C(fund))),
            "A": dict(zip(("score", "reason"), score_A(fund))),
            "N": dict(zip(("score", "reason"), score_N(bars))),
            "S": dict(zip(("score", "reason"), score_S(bars))),
            "L": dict(zip(("score", "reason"), score_L(bars, index_bars=index_bars))),
            "I": dict(zip(("score", "reason"), score_I(None))),
            "M": {"score": m_score, "reason": m_reason},
        }
        composite = 0.0
        for k, w in WEIGHTS.items():
            composite += components[k]["score"] * w
        score = int(round(composite))
        rows.append(CanslimRow(
            symbol=sec.symbol,
            sector=sec.sector_id,
            score=score,
            rating=_classify_rating(score),
            components=components,
        ))

    rows.sort(key=lambda r: r.score, reverse=True)

    # Apply per-sector cap to prevent hydropower domination
    if max_per_sector > 0:
        counts: dict[str, int] = {}
        kept: list[CanslimRow] = []
        for r in rows:
            n = counts.get(r.sector, 0)
            if n < max_per_sector:
                kept.append(r)
                counts[r.sector] = n + 1
        rows = kept

    return rows
