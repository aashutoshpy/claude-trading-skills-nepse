"""Tests for the NEPSE margin calculator."""

from dataclasses import replace

import pytest
from margin_calculator import (
    MarginRules,
    check_eligibility,
    compute_position,
    margin_call_price,
)

from common.nepse._config import reset_cache
from common.nepse.registry import Registry


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_cache()
    yield
    reset_cache()


@pytest.fixture
def rules():
    return MarginRules(enabled=True, initial_pct=30.0, maintenance_pct=20.0)


@pytest.fixture
def registry():
    return Registry.load()


@pytest.fixture
def registry_with_nabil_eligible(registry):
    # `Registry` is frozen; rebuild with NABIL added to margin set.
    new_set = frozenset({"NABIL"})
    return replace(registry, margin_eligible_symbols=new_set)


# ---- pure math: margin_call_price -----------------------------------------


def test_margin_call_price_formula():
    # shares=100, borrowed=70000, maintenance=20%
    # P_call = 70000 / (100 * 0.8) = 875.00
    assert margin_call_price(shares=100, borrowed=70_000, maintenance_pct=20.0) == 875.00


def test_margin_call_price_returns_none_for_zero_shares():
    assert margin_call_price(shares=0, borrowed=1000, maintenance_pct=20.0) is None


def test_margin_call_price_returns_none_for_invalid_maintenance():
    assert margin_call_price(shares=100, borrowed=1000, maintenance_pct=100.0) is None


# ---- check_eligibility ----------------------------------------------------


def test_eligible_when_on_list_and_rules_enabled(registry_with_nabil_eligible, rules):
    chk = check_eligibility("NABIL", registry=registry_with_nabil_eligible, rules=rules)
    assert chk.eligible is True
    assert chk.initial_pct == 30.0
    assert chk.maintenance_pct == 20.0


def test_not_eligible_when_off_list(registry_with_nabil_eligible, rules):
    chk = check_eligibility("UNKNOWN", registry=registry_with_nabil_eligible, rules=rules)
    assert chk.eligible is False


def test_not_eligible_when_rules_disabled(registry_with_nabil_eligible):
    disabled_rules = MarginRules(enabled=False, initial_pct=30.0, maintenance_pct=20.0)
    chk = check_eligibility("NABIL", registry=registry_with_nabil_eligible, rules=disabled_rules)
    assert chk.eligible is False


def test_case_insensitive(registry_with_nabil_eligible, rules):
    chk = check_eligibility("nabil", registry=registry_with_nabil_eligible, rules=rules)
    assert chk.eligible is True
    assert chk.symbol == "NABIL"


# ---- compute_position ----------------------------------------------------


def test_position_with_default_30pct_margin(registry_with_nabil_eligible, rules):
    rep = compute_position(
        "NABIL", entry_price=1000.0, shares=100,
        registry=registry_with_nabil_eligible, rules=rules,
    )
    assert rep.position_cost == 100_000
    assert rep.initial_equity == 30_000
    assert rep.borrowed == 70_000
    # 70000 / (100 * 0.8) = 875
    assert rep.margin_call_price == 875.00


def test_position_with_custom_margin_pct(registry_with_nabil_eligible, rules):
    rep = compute_position(
        "NABIL", entry_price=1000.0, shares=100, margin_pct=50.0,
        registry=registry_with_nabil_eligible, rules=rules,
    )
    assert rep.initial_equity == 50_000
    assert rep.borrowed == 50_000


def test_position_current_price_updates_equity_and_distance(
    registry_with_nabil_eligible, rules
):
    rep = compute_position(
        "NABIL", entry_price=1000.0, shares=100,
        current_price=950.0,
        registry=registry_with_nabil_eligible, rules=rules,
    )
    assert rep.current_value == 95_000
    assert rep.current_equity == 25_000   # 95000 - 70000
    # Distance to NPR 875 call from NPR 950 = (875-950)/950 * 100 = -7.89%
    assert rep.pct_distance_to_call == -7.89


def test_position_warns_when_not_eligible(registry, rules):
    rep = compute_position(
        "UNKNOWN", entry_price=1000.0, shares=100,
        registry=registry, rules=rules,
    )
    assert rep.eligible is False
    assert rep.warning is not None
    assert "not on margin-eligible list" in rep.warning


def test_position_warns_when_margin_call_breached(
    registry_with_nabil_eligible, rules
):
    rep = compute_position(
        "NABIL", entry_price=1000.0, shares=100,
        current_price=800.0,    # below 875 trigger
        registry=registry_with_nabil_eligible, rules=rules,
    )
    assert rep.warning is not None
    assert "MARGIN CALL TRIGGERED" in rep.warning
