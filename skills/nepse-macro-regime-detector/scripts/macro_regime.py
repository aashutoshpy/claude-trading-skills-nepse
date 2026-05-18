"""Pure-functional NEPSE macro regime classification.

Inputs are normalized as dicts. No I/O — the CLI loads the CSV + JSONs
and hands the parsed dicts here.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta
from io import StringIO

import _path_setup  # noqa: F401


@dataclass
class MacroInputs:
    """Time-varying macro values, all optional."""

    nrb_repo_pct: float | None = None
    rate_direction: str | None = None        # easing | tightening | neutral
    usd_npr_pct_change_30d: float | None = None
    nifty50_ytd_pct: float | None = None
    brent_ytd_pct: float | None = None
    gold_ytd_pct: float | None = None
    as_of: date | None = None                # most recent as_of across rows
    stale: bool = False                       # True if as_of > 35 days old


@dataclass
class MacroRegimeResult:
    as_of: date
    regime: str                              # RISK_ON / NEUTRAL / RISK_OFF / STAGFLATION
    inputs: MacroInputs
    breadth_regime: str | None
    sector_leader: str | None
    rationale: list[str] = field(default_factory=list)


def parse_macro_csv(text: str, *, today: date) -> MacroInputs:
    inputs = MacroInputs()
    reader = csv.DictReader(StringIO(text))
    latest: date | None = None
    for row in reader:
        key = (row.get("key") or "").strip().lower()
        value = (row.get("value") or "").strip()
        as_of_str = (row.get("as_of") or "").strip()
        try:
            as_of = date.fromisoformat(as_of_str) if as_of_str else None
        except ValueError:
            as_of = None
        if as_of and (latest is None or as_of > latest):
            latest = as_of

        if not key:
            continue
        if key == "rate_direction":
            inputs.rate_direction = value.lower() if value else None
        else:
            try:
                fval = float(value)
            except ValueError:
                continue
            if key == "nrb_repo_pct":
                inputs.nrb_repo_pct = fval
            elif key == "usd_npr_pct_change_30d":
                inputs.usd_npr_pct_change_30d = fval
            elif key == "nifty50_ytd_pct":
                inputs.nifty50_ytd_pct = fval
            elif key == "brent_ytd_pct":
                inputs.brent_ytd_pct = fval
            elif key == "gold_ytd_pct":
                inputs.gold_ytd_pct = fval

    inputs.as_of = latest
    if latest:
        inputs.stale = (today - latest) > timedelta(days=35)
    else:
        inputs.stale = True
    return inputs


def _classify(
    inputs: MacroInputs, *, breadth_regime: str | None
) -> tuple[str, list[str]]:
    """Coarse rule-based regime classification."""
    rationale: list[str] = []

    # Stagflation precedence
    if (
        inputs.rate_direction == "tightening"
        and (inputs.brent_ytd_pct or 0) > 15.0
        and (inputs.usd_npr_pct_change_30d or 0) < 0
    ):
        rationale.append("NRB tightening + Brent +15%+ YTD + NPR weakening → STAGFLATION")
        return "STAGFLATION", rationale

    if inputs.rate_direction == "tightening":
        rationale.append(f"NRB tightening (current repo {inputs.nrb_repo_pct or '?'}%)")
        if breadth_regime in ("BEAR_BROAD", "BEAR_NARROW"):
            rationale.append(f"NEPSE breadth = {breadth_regime}")
            return "RISK_OFF", rationale
        rationale.append(f"NEPSE breadth = {breadth_regime or 'unknown'}")
        return "RISK_OFF", rationale

    if inputs.rate_direction == "easing":
        rationale.append(f"NRB easing (current repo {inputs.nrb_repo_pct or '?'}%)")
        return "RISK_ON", rationale

    # Neutral rate direction → defer to breadth
    if breadth_regime == "BULL_BROAD":
        rationale.append("NRB neutral + NEPSE breadth BULL_BROAD")
        return "RISK_ON", rationale
    if breadth_regime in ("BEAR_BROAD", "BEAR_NARROW"):
        rationale.append(f"NRB neutral + NEPSE breadth {breadth_regime}")
        return "RISK_OFF", rationale
    rationale.append(f"NRB neutral + NEPSE breadth {breadth_regime or 'unknown'}")
    return "NEUTRAL", rationale


def detect_macro_regime(
    *,
    macro: MacroInputs,
    breadth_json: dict | None,
    sectors_json: dict | None,
    today: date,
) -> MacroRegimeResult:
    breadth_regime = breadth_json.get("regime") if breadth_json else None
    sector_leader = None
    if sectors_json:
        sectors = sectors_json.get("sectors") or []
        if sectors:
            # First-window leader
            primary_label = next(iter(sectors[0].get("ranks") or {}), None)
            if primary_label:
                ranked = sorted(
                    (s for s in sectors if primary_label in s.get("ranks", {})),
                    key=lambda s: s["ranks"][primary_label],
                )
                if ranked:
                    sector_leader = ranked[0].get("sector_id")

    regime, rationale = _classify(macro, breadth_regime=breadth_regime)
    if macro.stale:
        rationale.append(
            f"⚠ macro inputs stale (as_of {macro.as_of}); regime call low-confidence"
        )

    return MacroRegimeResult(
        as_of=today,
        regime=regime,
        inputs=macro,
        breadth_regime=breadth_regime,
        sector_leader=sector_leader,
        rationale=rationale,
    )
