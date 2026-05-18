"""Pure-functional NEPSE top-risk composite scoring.

Each component returns (score 0-100, reason). Final composite is a
weighted average. No I/O — caller passes parsed JSON dicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

WEIGHTS = {
    "distribution": 0.30,
    "divergence":   0.25,
    "microfinance": 0.20,
    "concentration": 0.15,
    "ath_proximity": 0.10,
}


@dataclass
class TopRiskResult:
    score: int                                # 0-100
    level: str                                # LOW / ELEVATED / HIGH / EXTREME
    components: dict[str, dict] = field(default_factory=dict)


def _classify_level(score: int) -> str:
    if score <= 30:
        return "LOW"
    if score <= 55:
        return "ELEVATED"
    if score <= 75:
        return "HIGH"
    return "EXTREME"


# ---- component scorers ----------------------------------------------------


def score_distribution(distribution_json: dict | None) -> tuple[int, str]:
    if not distribution_json:
        return 0, "no distribution data"
    active = int(distribution_json.get("active_count", 0))
    # 0-2 = 0; 3 = 40; 4 = 65; 5 = 85; 6+ = 100
    table = {0: 0, 1: 10, 2: 20, 3: 40, 4: 65, 5: 85}
    score = table.get(active, 100 if active >= 6 else 0)
    return score, f"{active} active distribution days"


def score_divergence(uptrend_json: dict | None) -> tuple[int, str]:
    if not uptrend_json:
        return 0, "no uptrend data"
    if uptrend_json.get("divergence_detected"):
        return 80, uptrend_json.get("divergence_note", "divergence detected")
    return 0, "no divergence"


def score_microfinance_leadership(sectors_json: dict | None) -> tuple[int, str]:
    if not sectors_json:
        return 0, "no sector data"
    sectors = sectors_json.get("sectors") or []
    # Find MICROFINANCE rank in the first/primary window
    mf = next((s for s in sectors if s.get("sector_id") == "MICROFINANCE"), None)
    if not mf or not mf.get("ranks"):
        return 0, "microfinance not ranked"
    # First-window rank
    first_window_label = next(iter(mf["ranks"]))
    rank = mf["ranks"][first_window_label]
    if rank == 1:
        return 70, f"microfinance #1 in {first_window_label}"
    if rank == 2:
        return 40, f"microfinance #2 in {first_window_label}"
    return 10, f"microfinance #{rank} in {first_window_label}"


def score_concentration(breadth_json: dict | None) -> tuple[int, str]:
    """Score 0-100 by how concentrated the day's advances are in a single sector."""
    if not breadth_json:
        return 0, "no breadth data"
    breakdown = breadth_json.get("sector_breakdown") or {}
    total_adv = sum(s.get("advances", 0) for s in breakdown.values())
    if total_adv == 0:
        return 0, "no advances today"
    max_sector = max(breakdown.values(), key=lambda s: s.get("advances", 0))
    max_share = max_sector.get("advances", 0) / total_adv * 100.0
    # Find the sector name
    sector_name = next(
        (sid for sid, s in breakdown.items() if s is max_sector), "?"
    )
    if max_share >= 60:
        return 80, f"{sector_name} accounts for {max_share:.0f}% of advances (very concentrated)"
    if max_share >= 50:
        return 55, f"{sector_name} accounts for {max_share:.0f}% of advances"
    if max_share >= 40:
        return 25, f"{sector_name} accounts for {max_share:.0f}% of advances"
    return 0, f"max-sector share {max_share:.0f}% (broad participation)"


def score_ath_proximity(uptrend_json: dict | None) -> tuple[int, str]:
    """Score 0-100 by how close current uptrend ratio is to its 1-year peak.

    A ratio sitting AT its 1-year peak with high absolute value is more
    top-risk than the same ratio mid-cycle.
    """
    if not uptrend_json:
        return 0, "no uptrend data"
    history = uptrend_json.get("history") or []
    if not history:
        return 0, "no history"
    current = float(uptrend_json.get("current_ratio", 0))
    peak = max(float(p.get("ratio", 0)) for p in history)
    if peak <= 0:
        return 0, "history peak is 0"
    proximity_pct = current / peak * 100.0
    if current >= 70 and proximity_pct >= 95:
        return 70, f"current ratio {current}% within 5% of 1y peak ({peak}%)"
    if current >= 70 and proximity_pct >= 85:
        return 40, f"current ratio {current}% within 15% of 1y peak"
    return 10, f"current ratio {current}% vs 1y peak {peak}%"


# ---- aggregator ----------------------------------------------------------


def compute_top_risk(
    *,
    distribution_json: dict | None,
    uptrend_json: dict | None,
    sectors_json: dict | None,
    breadth_json: dict | None,
) -> TopRiskResult:
    components = {
        "distribution": dict(zip(("score", "reason"), score_distribution(distribution_json))),
        "divergence":   dict(zip(("score", "reason"), score_divergence(uptrend_json))),
        "microfinance": dict(zip(("score", "reason"), score_microfinance_leadership(sectors_json))),
        "concentration": dict(zip(("score", "reason"), score_concentration(breadth_json))),
        "ath_proximity": dict(zip(("score", "reason"), score_ath_proximity(uptrend_json))),
    }
    total = 0.0
    for key, weight in WEIGHTS.items():
        total += components[key]["score"] * weight
    score = int(round(total))
    return TopRiskResult(score=score, level=_classify_level(score), components=components)
