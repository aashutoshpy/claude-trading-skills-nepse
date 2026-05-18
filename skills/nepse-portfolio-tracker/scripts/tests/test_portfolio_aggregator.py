"""Tests for the NEPSE portfolio aggregator."""

from dataclasses import replace
from datetime import date

import pytest
from portfolio_aggregator import (
    Position,
    build_snapshot,
    parse_portfolio_csv,
)

from common.nepse._config import reset_cache
from common.nepse.registry import Registry


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_cache()
    yield
    reset_cache()


@pytest.fixture
def registry():
    return Registry.load()


@pytest.fixture
def registry_with_nabil_margin(registry):
    return replace(registry, margin_eligible_symbols=frozenset({"NABIL"}))


# ---- CSV parsing ------------------------------------------------------


def test_parse_csv_basic():
    csv = (
        "symbol,shares,avg_cost,entry_date,is_margin\n"
        "NABIL,100,1180.00,2026-02-15,false\n"
        "UPPER,200,425.00,2026-03-22,true\n"
    )
    positions = parse_portfolio_csv(csv)
    by_sym = {p.symbol: p for p in positions}
    assert by_sym["NABIL"].shares == 100
    assert by_sym["NABIL"].avg_cost == 1180.0
    assert by_sym["NABIL"].is_margin is False
    assert by_sym["UPPER"].is_margin is True


def test_parse_csv_skips_zero_shares():
    csv = "symbol,shares,avg_cost\nNABIL,0,1180\nUPPER,100,425\n"
    positions = parse_portfolio_csv(csv)
    assert [p.symbol for p in positions] == ["UPPER"]


def test_parse_csv_handles_missing_optional_fields():
    csv = "symbol,shares,avg_cost\nNABIL,100,1180\n"
    positions = parse_portfolio_csv(csv)
    assert positions[0].entry_date is None
    assert positions[0].is_margin is False


def test_parse_csv_bad_numeric_skipped():
    csv = "symbol,shares,avg_cost\nBAD,oops,1180\nOK,100,1180\n"
    positions = parse_portfolio_csv(csv)
    assert [p.symbol for p in positions] == ["OK"]


def test_parse_csv_is_margin_variants():
    csv = "symbol,shares,avg_cost,is_margin\nA,1,100,true\nB,1,100,1\nC,1,100,yes\nD,1,100,no\n"
    positions = parse_portfolio_csv(csv)
    by_sym = {p.symbol: p.is_margin for p in positions}
    assert by_sym["A"] is True
    assert by_sym["B"] is True
    assert by_sym["C"] is True
    assert by_sym["D"] is False


# ---- build_snapshot --------------------------------------------------


def test_snapshot_computes_totals_with_live_prices(registry):
    positions = [
        Position("NABIL", 100, 1180.0),
        Position("UPPER", 200, 425.0),
    ]
    prices = {"NABIL": 1245.0, "UPPER": 410.0}
    s = build_snapshot(positions, price_lookup=prices, registry=registry, today=date(2026, 5, 17))
    # Invested: 100*1180 + 200*425 = 203000
    assert s.invested_total == 203_000
    # Current: 100*1245 + 200*410 = 206500
    assert s.current_value_total == 206_500
    assert s.unrealized_pnl_npr == 3_500
    assert s.unrealized_pnl_pct == round(3500 / 203000 * 100, 2)


def test_snapshot_uses_avg_cost_when_price_missing(registry):
    positions = [Position("UNKNOWN", 100, 100.0)]
    s = build_snapshot(positions, price_lookup={}, registry=registry, today=date(2026, 5, 17))
    assert s.positions[0].current_price == 100.0
    assert s.positions[0].unrealized_pnl_pct == 0.0


def test_snapshot_margin_call_distance_for_margin_position(registry_with_nabil_margin):
    positions = [Position("NABIL", 100, 1000.0, is_margin=True)]
    # avg_cost 1000, 30% initial → borrowed = 70000
    # call price = 70000 / (100 * 0.8) = 875.00
    prices = {"NABIL": 950.0}
    s = build_snapshot(
        positions, price_lookup=prices, registry=registry_with_nabil_margin,
        today=date(2026, 5, 17),
    )
    p = s.positions[0]
    assert p.margin_call_price == 875.00
    # Distance from 950 to 875 = (875-950)/950 * 100 = -7.89
    assert p.margin_call_distance_pct == -7.89


def test_snapshot_warns_when_margin_flag_but_not_eligible(registry):
    positions = [Position("UNKNOWN", 100, 1000.0, is_margin=True)]
    s = build_snapshot(positions, price_lookup={"UNKNOWN": 1000.0}, registry=registry,
                       today=date(2026, 5, 17))
    assert any("NOT on margin-eligible" in w for w in s.positions[0].warnings)


def test_snapshot_warns_when_margin_call_breached(registry_with_nabil_margin):
    positions = [Position("NABIL", 100, 1000.0, is_margin=True)]
    # Current price 800 < margin call 875 → triggered
    s = build_snapshot(positions, price_lookup={"NABIL": 800.0}, registry=registry_with_nabil_margin,
                       today=date(2026, 5, 17))
    assert any("TRIGGERED" in w for w in s.positions[0].warnings)
    assert any("margin call active" in w for w in s.margin_warnings)


def test_snapshot_sector_breakdown_percentages_sum(registry):
    positions = [Position("A", 100, 100.0), Position("B", 100, 100.0)]
    s = build_snapshot(positions, price_lookup={"A": 100.0, "B": 100.0},
                       registry=registry, today=date(2026, 5, 17))
    total_pct = sum(entry["value_pct"] for entry in s.sector_breakdown.values())
    assert round(total_pct, 0) == 100


def test_snapshot_flags_sector_concentration():
    # Single sector dominates → triggers warning
    positions = [Position(f"X{i}", 100, 100.0) for i in range(5)]
    s = build_snapshot(
        positions, price_lookup={f"X{i}": 100.0 for i in range(5)},
        registry=Registry.load(), today=date(2026, 5, 17),
    )
    # All map to OTHERS by default → 100% in OTHERS → warning
    assert s.sector_warnings != []
