"""Pure-functional NEPSE Druckenmiller-style bias synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field

import _path_setup  # noqa: F401

WEIGHTS = {
    "nrb":           0.20,
    "uptrend":       0.15,
    "breadth":       0.15,
    "sector_clarity": 0.10,
    "top_risk":      0.15,
    "distribution":  0.10,
    "usd_npr":       0.08,
    "nifty50":       0.07,
}


@dataclass
class DruckResult:
    score: int
    bias: str
    tilt: dict
    components: dict[str, dict] = field(default_factory=dict)


# ---- component scorers (each returns 0-100) -----------------------------


def _score_nrb(macro_json: dict | None) -> tuple[int, str]:
    if not macro_json:
        return 50, "no macro data"
    inputs = macro_json.get("inputs") or {}
    direction = inputs.get("rate_direction") or "neutral"
    return {
        "easing":     (90, "NRB easing — cycle tailwind"),
        "neutral":    (55, "NRB neutral"),
        "tightening": (15, "NRB tightening — cycle headwind"),
    }.get(direction, (50, f"unknown direction: {direction}"))


def _score_uptrend(uptrend_json: dict | None) -> tuple[int, str]:
    if not uptrend_json:
        return 50, "no uptrend data"
    return {
        "STRONG_UPTREND": (95, "strong uptrend"),
        "UPTREND":        (75, "uptrend"),
        "NEUTRAL":        (45, "neutral regime"),
        "DOWNTREND":      (10, "downtrend"),
    }.get(uptrend_json.get("regime"), (50, "unknown regime"))


def _score_breadth(breadth_json: dict | None) -> tuple[int, str]:
    if not breadth_json:
        return 50, "no breadth data"
    return {
        "BULL_BROAD":  (90, "broad bull regime"),
        "BULL_NARROW": (70, "narrow bull regime"),
        "NEUTRAL":     (50, "neutral breadth"),
        "BEAR_NARROW": (25, "narrow bear regime"),
        "BEAR_BROAD":  (10, "broad bear regime"),
    }.get(breadth_json.get("regime"), (50, "unknown regime"))


def _score_sector_clarity(sectors_json: dict | None) -> tuple[int, str]:
    """Strong sector leadership = clear cycle; flat ranks = no edge."""
    if not sectors_json:
        return 50, "no sector data"
    sectors = sectors_json.get("sectors") or []
    if not sectors:
        return 50, "no sectors"
    first_window = next(iter(sectors[0].get("returns_pct", {})), None)
    if not first_window:
        return 50, "no return data"
    returns = sorted(
        [s["returns_pct"].get(first_window, 0) for s in sectors if first_window in s.get("returns_pct", {})],
        reverse=True,
    )
    if len(returns) < 3:
        return 50, "too few sectors"
    spread = returns[0] - returns[-1]
    if spread >= 10:
        return 85, f"clear leadership (top-bottom spread {spread:.1f}%)"
    if spread >= 5:
        return 65, f"moderate leadership (spread {spread:.1f}%)"
    return 40, f"flat sector rotation (spread {spread:.1f}%)"


def _score_top_risk(top_json: dict | None) -> tuple[int, str]:
    """High top risk → lower bias score."""
    if not top_json:
        return 50, "no top-risk data"
    level = top_json.get("level")
    return {
        "LOW":      (90, "low top risk"),
        "ELEVATED": (60, "elevated top risk"),
        "HIGH":     (30, "high top risk"),
        "EXTREME":  (5,  "extreme top risk — exit signals"),
    }.get(level, (50, "unknown level"))


def _score_distribution(distrib_json: dict | None) -> tuple[int, str]:
    if not distrib_json:
        return 50, "no distribution-day data"
    active = int(distrib_json.get("active_count", 0))
    if active <= 1:
        return 90, f"{active} distribution days"
    if active <= 3:
        return 60, f"{active} distribution days"
    if active <= 4:
        return 30, f"{active} distribution days"
    return 5, f"{active} distribution days"


def _score_usd_npr(macro_json: dict | None) -> tuple[int, str]:
    if not macro_json:
        return 50, "no FX data"
    inputs = macro_json.get("inputs") or {}
    pct = inputs.get("usd_npr_pct_change_30d")
    if pct is None:
        return 50, "no USD/NPR data"
    if pct > 0:
        return 65, f"NPR strengthening ({pct:+.1f}% 30d) — risk-on tailwind"
    if pct < -1.5:
        return 25, f"NPR weakening sharply ({pct:+.1f}% 30d) — risk-off"
    return 50, f"NPR roughly flat ({pct:+.1f}% 30d)"


def _score_nifty(macro_json: dict | None) -> tuple[int, str]:
    if not macro_json:
        return 50, "no Nifty data"
    inputs = macro_json.get("inputs") or {}
    ytd = inputs.get("nifty50_ytd_pct")
    if ytd is None:
        return 50, "no Nifty data"
    if ytd >= 10:
        return 80, f"India Nifty +{ytd:.0f}% YTD — regional risk-on"
    if ytd >= 0:
        return 60, f"India Nifty +{ytd:.0f}% YTD"
    return 30, f"India Nifty {ytd:.0f}% YTD — regional risk-off"


# ---- aggregator -------------------------------------------------------


def _classify_bias(score: int) -> str:
    if score >= 80:
        return "STRONG_BIAS_LONG"
    if score >= 60:
        return "BIAS_LONG"
    if score >= 40:
        return "NEUTRAL"
    if score >= 20:
        return "BIAS_DEFENSIVE"
    return "STRONG_DEFENSIVE"


def _tilt_for(bias: str) -> dict:
    return {
        "STRONG_BIAS_LONG": {
            "exposure_pct_range": "90-100%",
            "name_count_range": "5-8",
            "sector_tilt": "concentrate in top sectors per nepse-sector-analyst",
        },
        "BIAS_LONG": {
            "exposure_pct_range": "70-85%",
            "name_count_range": "8-12",
            "sector_tilt": "favor leaders; defensive ballast",
        },
        "NEUTRAL": {
            "exposure_pct_range": "50-70%",
            "name_count_range": "10-15",
            "sector_tilt": "diversified BFI / hydropower / insurance",
        },
        "BIAS_DEFENSIVE": {
            "exposure_pct_range": "30-50%",
            "name_count_range": "5-8",
            "sector_tilt": "insurance + top-quality dividend BFIs only",
        },
        "STRONG_DEFENSIVE": {
            "exposure_pct_range": "0-25%",
            "name_count_range": "0-3",
            "sector_tilt": "cash; one or two defensive holdings only",
        },
    }[bias]


def synthesize(
    *,
    macro_json: dict | None,
    uptrend_json: dict | None,
    breadth_json: dict | None,
    sectors_json: dict | None,
    top_json: dict | None,
    distrib_json: dict | None,
) -> DruckResult:
    components = {
        "nrb":            dict(zip(("score", "reason"), _score_nrb(macro_json))),
        "uptrend":        dict(zip(("score", "reason"), _score_uptrend(uptrend_json))),
        "breadth":        dict(zip(("score", "reason"), _score_breadth(breadth_json))),
        "sector_clarity": dict(zip(("score", "reason"), _score_sector_clarity(sectors_json))),
        "top_risk":       dict(zip(("score", "reason"), _score_top_risk(top_json))),
        "distribution":   dict(zip(("score", "reason"), _score_distribution(distrib_json))),
        "usd_npr":        dict(zip(("score", "reason"), _score_usd_npr(macro_json))),
        "nifty50":        dict(zip(("score", "reason"), _score_nifty(macro_json))),
    }
    total = 0.0
    for k, w in WEIGHTS.items():
        total += components[k]["score"] * w
    score = int(round(total))
    bias = _classify_bias(score)
    return DruckResult(score=score, bias=bias, tilt=_tilt_for(bias), components=components)
