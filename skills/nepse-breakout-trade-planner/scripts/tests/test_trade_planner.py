"""Tests for the NEPSE breakout trade planner."""

from trade_planner import AccountSettings, plan_all, plan_one


def _candidate(**overrides) -> dict:
    base = {
        "symbol": "NABIL",
        "sector": "BANKING",
        "price": 1245.0,
        "pivot_price": 1252.0,
        "composite_score": 78,
        "valid_vcp": True,
        "distance_to_pivot_pct": 0.6,
        "margin_eligible": True,
    }
    base.update(overrides)
    return base


def _acct(account_size=1_000_000, risk_pct=1.0, stop_pct=7.0) -> AccountSettings:
    return AccountSettings(account_size=account_size, risk_pct=risk_pct, stop_pct=stop_pct)


# ---- plan_one ----------------------------------------------------------


def test_plan_one_basic_arithmetic():
    p = plan_one(_candidate(), account=_acct())
    # entry = pivot * 1.001 = 1253.252 → round 1253.25
    assert p.entry_trigger == 1253.25
    # stop = entry * 0.93 = 1165.5225 → round 1165.52
    assert p.stop_loss == 1165.52
    # risk/share = 87.73
    assert p.risk_per_share == 87.73
    # risk budget = 1000000 * 1% = 10000 → 10000 / 87.73 ≈ 113.97 → 113 shares
    assert p.shares == 113
    assert p.position_cost == round(1253.25 * 113, 2)
    assert p.target_1r == round(1253.25 + 87.73, 2)
    assert p.target_2r == round(1253.25 + 2 * 87.73, 2)
    assert p.target_3r == round(1253.25 + 3 * 87.73, 2)


def test_plan_one_returns_none_for_missing_symbol():
    assert plan_one({"pivot_price": 100.0, "price": 99.0}, account=_acct()) is None


def test_plan_one_returns_none_for_zero_pivot():
    assert plan_one(_candidate(pivot_price=0), account=_acct()) is None


def test_plan_one_imminent_entry_warning():
    p = plan_one(_candidate(distance_to_pivot_pct=0.3), account=_acct())
    assert any("imminent" in w for w in p.warnings)


def test_plan_one_oversized_position_warning():
    # Account = 4,000 NPR, risk_pct = 3% → risk budget = 120 NPR
    # 120 / 87.73 = 1.37 → floor = 1 share
    # 1 share × NPR 1253.25 = 31.3% of 4000 — triggers the >25% warning
    p = plan_one(_candidate(), account=_acct(account_size=4_000, risk_pct=3.0))
    assert p is not None
    assert p.shares == 1
    assert p.position_pct_of_account > 25
    assert any("would be" in w for w in p.warnings)


def test_plan_one_returns_none_when_size_floors_to_zero():
    # Risk budget = 1 NPR; risk/share = 87.73 → 0.01 shares → floor 0 → None
    assert plan_one(_candidate(), account=_acct(account_size=100, risk_pct=1.0)) is None


def test_plan_one_invalid_vcp_warning():
    p = plan_one(_candidate(valid_vcp=False), account=_acct())
    assert any("validity flag" in w for w in p.warnings)


def test_plan_one_amo_instruction_includes_entry_price():
    p = plan_one(_candidate(), account=_acct())
    assert "1253.25" in p.amo_instruction
    assert "18:00" in p.amo_instruction


# ---- plan_all ----------------------------------------------------------


def test_plan_all_filters_by_min_score():
    candidates = [
        _candidate(symbol="HIGH", composite_score=80),
        _candidate(symbol="LOW", composite_score=40),
    ]
    plans = plan_all(candidates, account=_acct(), min_score=60)
    assert [p.symbol for p in plans] == ["HIGH"]


def test_plan_all_filters_valid_only():
    candidates = [
        _candidate(symbol="OK", valid_vcp=True),
        _candidate(symbol="INVALID", valid_vcp=False),
    ]
    plans = plan_all(candidates, account=_acct(), min_score=0, valid_only=True)
    assert [p.symbol for p in plans] == ["OK"]


def test_plan_all_sorts_by_score_descending():
    candidates = [
        _candidate(symbol="LOWER", composite_score=70),
        _candidate(symbol="HIGHER", composite_score=85),
    ]
    plans = plan_all(candidates, account=_acct(), min_score=0)
    assert [p.symbol for p in plans] == ["HIGHER", "LOWER"]
