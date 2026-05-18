"""Pure-functional NEPSE theme detection.

Themes are static definitions (built-in or user-supplied). The engine
scores each theme using the latest sector + breadth + macro JSONs.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO

import _path_setup  # noqa: F401


@dataclass
class Theme:
    theme_id: str
    display_name: str
    symbols: list[str]
    primary_sectors: list[str]            # sector_ids that drive this theme
    favorable_macro: list[str]            # macro regimes that favor it
    rationale: str = ""


@dataclass
class ThemeScore:
    theme: Theme
    score: int                            # 0-100
    status: str                           # ACTIVE / DEVELOPING / INACTIVE
    components: dict[str, dict] = field(default_factory=dict)


BUILT_IN_THEMES: list[Theme] = [
    Theme(
        theme_id="monsoon_hydropower",
        display_name="Monsoon Hydropower",
        symbols=["UPPER", "NHPC", "BPCL", "AHPC", "BARUN"],
        primary_sectors=["HYDROPOWER"],
        favorable_macro=["RISK_ON", "NEUTRAL"],
        rationale="June-September generation peak; PPA / electricity-export catalysts",
    ),
    Theme(
        theme_id="rate_cut_financials",
        display_name="Rate-Cut Financials",
        symbols=["NABIL", "NIB", "SCB", "NICA", "EBL", "SBI"],
        primary_sectors=["BANKING", "FINANCE"],
        favorable_macro=["RISK_ON"],
        rationale="NRB easing cycle expands net interest margins",
    ),
    Theme(
        theme_id="defensive_insurance",
        display_name="Defensive Insurance",
        symbols=["NLIC", "LICN", "NICL", "RLI", "SLI"],
        primary_sectors=["LIFE_INSURANCE", "NON_LIFE_INSURANCE"],
        favorable_macro=["RISK_OFF", "NEUTRAL"],
        rationale="Rate-sensitive defensive rotation when composite weakens",
    ),
    Theme(
        theme_id="microfinance_speculation",
        display_name="Microfinance Speculation",
        symbols=["CBBL", "GBLBS", "NSEWA", "SHL"],
        primary_sectors=["MICROFINANCE"],
        favorable_macro=["RISK_ON"],
        rationale="Late-cycle / speculative momentum; high beta",
    ),
    Theme(
        theme_id="bfi_dividend_cluster",
        display_name="BFI Dividend Cluster",
        symbols=["NABIL", "NICA", "EBL", "SBI"],
        primary_sectors=["BANKING"],
        favorable_macro=["RISK_ON", "NEUTRAL"],
        rationale="Bhadra-Mangsir AGM season cash dividend distributions",
    ),
]


def parse_themes_csv(text: str) -> list[Theme]:
    """Parse a user theme CSV with columns: theme_id, display_name, symbols, rationale.

    Optional columns: primary_sectors (comma-sep), favorable_macro (comma-sep).
    """
    out: list[Theme] = []
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        tid = (row.get("theme_id") or "").strip()
        if not tid:
            continue
        out.append(Theme(
            theme_id=tid,
            display_name=(row.get("display_name") or tid).strip(),
            symbols=[s.strip().upper() for s in (row.get("symbols") or "").split(",") if s.strip()],
            primary_sectors=[s.strip().upper() for s in (row.get("primary_sectors") or "").split(",") if s.strip()],
            favorable_macro=[s.strip().upper() for s in (row.get("favorable_macro") or "").split(",") if s.strip()],
            rationale=(row.get("rationale") or "").strip(),
        ))
    return out


# ---- scoring -------------------------------------------------------------


def _score_sector_alignment(theme: Theme, sectors_json: dict | None) -> tuple[int, str]:
    if not sectors_json or not theme.primary_sectors:
        return 0, "no sector data"
    sectors = sectors_json.get("sectors") or []
    # Use first window's ranks
    first_window = None
    for s in sectors:
        if s.get("ranks"):
            first_window = next(iter(s["ranks"].keys()))
            break
    if not first_window:
        return 0, "no rank data"

    # Find best rank among the theme's primary sectors
    best_rank: int | None = None
    for s in sectors:
        if s.get("sector_id") in theme.primary_sectors:
            r = s.get("ranks", {}).get(first_window)
            if r is not None and (best_rank is None or r < best_rank):
                best_rank = r

    if best_rank is None:
        return 0, "theme sectors not ranked"
    if best_rank == 1:
        return 40, f"primary sector ranked #1 in {first_window}"
    if best_rank == 2:
        return 30, f"primary sector ranked #2 in {first_window}"
    if best_rank == 3:
        return 22, f"primary sector ranked #3 in {first_window}"
    if best_rank <= 5:
        return 12, f"primary sector ranked #{best_rank} in {first_window}"
    return 5, f"primary sector ranked #{best_rank} in {first_window}"


def _score_macro_alignment(theme: Theme, macro_json: dict | None) -> tuple[int, str]:
    if not macro_json or not theme.favorable_macro:
        return 12, "no macro data"
    regime = macro_json.get("regime")
    if regime in theme.favorable_macro:
        return 25, f"macro regime `{regime}` is favorable"
    return 0, f"macro regime `{regime}` not favorable"


def _score_breadth_alignment(theme: Theme, breadth_json: dict | None) -> tuple[int, str]:
    if not breadth_json or not theme.primary_sectors:
        return 10, "no breadth data"
    breakdown = breadth_json.get("sector_breakdown") or {}
    total_adv = sum(s.get("advances", 0) for s in breakdown.values())
    if total_adv == 0:
        return 0, "no advances today"
    theme_adv = sum(
        breakdown.get(sid, {}).get("advances", 0) for sid in theme.primary_sectors
    )
    share = theme_adv / total_adv * 100.0
    if share >= 40:
        return 20, f"theme sectors = {share:.0f}% of advances"
    if share >= 20:
        return 12, f"theme sectors = {share:.0f}% of advances"
    return 4, f"theme sectors = {share:.0f}% of advances"


def _score_recency(theme: Theme, uptrend_json: dict | None) -> tuple[int, str]:
    """If uptrend ratio is rising, themes are more likely working."""
    if not uptrend_json:
        return 8, "no uptrend data"
    regime = uptrend_json.get("regime")
    if regime == "STRONG_UPTREND":
        return 15, "strong uptrend regime"
    if regime == "UPTREND":
        return 11, "uptrend regime"
    if regime == "NEUTRAL":
        return 6, "neutral regime"
    return 0, "downtrend regime — themes unreliable"


def _classify_status(score: int) -> str:
    if score >= 70:
        return "ACTIVE"
    if score >= 50:
        return "DEVELOPING"
    return "INACTIVE"


def score_themes(
    themes: list[Theme],
    *,
    sectors_json: dict | None,
    breadth_json: dict | None,
    macro_json: dict | None,
    uptrend_json: dict | None,
) -> list[ThemeScore]:
    out: list[ThemeScore] = []
    for t in themes:
        components = {
            "sector": dict(zip(("score", "reason"), _score_sector_alignment(t, sectors_json))),
            "macro":  dict(zip(("score", "reason"), _score_macro_alignment(t, macro_json))),
            "breadth": dict(zip(("score", "reason"), _score_breadth_alignment(t, breadth_json))),
            "recency": dict(zip(("score", "reason"), _score_recency(t, uptrend_json))),
        }
        score = sum(c["score"] for c in components.values())
        out.append(ThemeScore(theme=t, score=score, status=_classify_status(score), components=components))
    out.sort(key=lambda ts: ts.score, reverse=True)
    return out
