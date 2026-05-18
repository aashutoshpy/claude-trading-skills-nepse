"""NEPSE universe + sector taxonomy + margin eligibility loader.

Sector identifiers are stable string IDs (e.g. `HYDROPOWER`) so screening
code can rely on them. Display names ("Hydropower") come from
`config/registry.yaml`.
"""

from __future__ import annotations

from dataclasses import dataclass

from common.nepse._config import NepseConfigError, load_registry_yaml


@dataclass(frozen=True)
class Sector:
    id: str
    display_name: str
    approximate_count: int | None = None


@dataclass(frozen=True)
class Registry:
    """View over `config/registry.yaml` — construct via `Registry.load()`."""

    sectors: tuple[Sector, ...]
    listed_company_count_seed: int
    margin_eligible_symbols: frozenset[str]
    fiscal_year_label: str
    fiscal_quarter_ends: tuple[tuple[int, str], ...]  # [(q, gregorian_iso), ...]

    @classmethod
    def load(cls) -> Registry:
        data = load_registry_yaml()
        try:
            sectors = tuple(_parse_sector(s) for s in data["sectors"])
            fy = data["nepali_fiscal_year"]
            quarters = tuple((int(q["q"]), str(q["ends_gregorian"])) for q in fy["quarters"])
            return cls(
                sectors=sectors,
                listed_company_count_seed=int(data.get("listed_company_count_seed", 0)),
                margin_eligible_symbols=frozenset(data.get("margin_eligible_symbols") or []),
                fiscal_year_label=str(fy["fy_label"]),
                fiscal_quarter_ends=quarters,
            )
        except KeyError as exc:
            raise NepseConfigError(f"registry.yaml is missing required key: {exc}") from exc

    # ---- queries ----------------------------------------------------------

    def sector_by_id(self, sector_id: str) -> Sector:
        for s in self.sectors:
            if s.id == sector_id:
                return s
        raise KeyError(f"Unknown NEPSE sector id: {sector_id!r}")

    def is_margin_eligible(self, symbol: str) -> bool:
        return symbol.upper() in self.margin_eligible_symbols


def _parse_sector(raw: dict) -> Sector:
    try:
        return Sector(
            id=str(raw["id"]),
            display_name=str(raw["display_name"]),
            approximate_count=int(raw["approximate_count"]) if "approximate_count" in raw else None,
        )
    except KeyError as exc:
        raise NepseConfigError(f"sector entry missing key: {exc}") from exc
