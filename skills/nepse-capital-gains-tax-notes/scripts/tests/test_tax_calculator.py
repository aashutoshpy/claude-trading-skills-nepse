"""Tests for the NEPSE capital gains tax calculator."""

import pytest
from tax_calculator import TaxRates, estimate_tax

from common.nepse._config import reset_cache


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_cache()
    yield
    reset_cache()


@pytest.fixture
def rates():
    return TaxRates.load()


def test_rates_loaded_from_config(rates):
    assert rates.long_term_pct == 5.0
    assert rates.short_term_pct == 7.5
    assert rates.long_term_threshold_days == 365
    assert rates.proposed_uniform_status == "not_enacted"


def test_short_term_uses_7_5_pct(rates):
    est = estimate_tax(
        symbol="NABIL", entry_price=1180.0, exit_price=1340.0,
        shares=100, holding_days=280, rates=rates,
    )
    assert est.is_long_term is False
    assert est.rate_pct == 7.5
    assert est.cost == 118_000
    assert est.proceeds == 134_000
    assert est.gross_gain == 16_000
    assert est.tax_npr == round(16_000 * 0.075, 2)
    assert est.net_gain == 14_800


def test_long_term_uses_5_pct(rates):
    est = estimate_tax(
        symbol="NABIL", entry_price=1180.0, exit_price=1340.0,
        shares=100, holding_days=400, rates=rates,
    )
    assert est.is_long_term is True
    assert est.rate_pct == 5.0
    assert est.tax_npr == round(16_000 * 0.05, 2)


def test_threshold_is_strictly_greater_than_365(rates):
    est_365 = estimate_tax(
        symbol="X", entry_price=100, exit_price=110, shares=1,
        holding_days=365, rates=rates,
    )
    est_366 = estimate_tax(
        symbol="X", entry_price=100, exit_price=110, shares=1,
        holding_days=366, rates=rates,
    )
    assert est_365.is_long_term is False
    assert est_366.is_long_term is True


def test_capital_loss_zero_tax_with_note(rates):
    est = estimate_tax(
        symbol="LOSS", entry_price=100, exit_price=80, shares=10,
        holding_days=200, rates=rates,
    )
    assert est.gross_gain == -200
    assert est.tax_npr == 0
    assert any("capital loss" in n for n in est.notes)


def test_days_to_lt_suggests_holding():
    rates = TaxRates(
        long_term_pct=5.0, short_term_pct=7.5, long_term_threshold_days=365,
        proposed_uniform_pct=10.0, proposed_uniform_status="not_enacted",
    )
    est = estimate_tax(
        symbol="X", entry_price=100, exit_price=110, shares=100,
        holding_days=300, rates=rates,
    )
    # days_to_lt = 365 + 1 - 300 = 66
    assert est.days_to_long_term == 66
    # ST tax = 75; LT tax = 50; savings = 25
    assert est.long_term_tax_npr == 50.0
    assert any("66 more days" in n for n in est.notes)
    assert any("savings" in n for n in est.notes)


def test_net_return_pct_uses_cost(rates):
    est = estimate_tax(
        symbol="X", entry_price=100, exit_price=110, shares=10,
        holding_days=200, rates=rates,
    )
    # gross = 100, tax = 7.5, net = 92.5, cost = 1000 → 9.25%
    assert est.net_return_pct == 9.25
