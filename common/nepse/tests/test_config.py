"""Smoke tests for the config loader."""

import pytest

from common.nepse._config import load_registry_yaml, load_rules, reset_cache


@pytest.fixture(autouse=True)
def _reset():
    reset_cache()
    yield
    reset_cache()


def test_rules_yaml_loads_with_required_keys():
    rules = load_rules()
    assert rules["market"] == "NEPSE"
    assert rules["trading_days_isoweekday"] == [1, 2, 3, 4, 5]
    assert rules["daily_price_band_pct"] == 15.0
    assert rules["session"]["open"] == "11:00"
    assert rules["session"]["close"] == "15:00"
    assert rules["settlement_t_plus"] == 2
    assert rules["short_selling_enabled"] is False
    assert rules["margin"]["enabled"] is True
    assert rules["capital_gains_tax"]["long_term_pct"] == 5.0


def test_registry_yaml_loads_with_thirteen_sectors():
    data = load_registry_yaml()
    sector_ids = [s["id"] for s in data["sectors"]]
    assert len(sector_ids) == 13
    for required in (
        "BANKING",
        "DEVELOPMENT_BANK",
        "HYDROPOWER",
        "MICROFINANCE",
        "LIFE_INSURANCE",
        "NON_LIFE_INSURANCE",
    ):
        assert required in sector_ids
    # Spot-check hydropower is the largest sector by approximate_count
    hp = next(s for s in data["sectors"] if s["id"] == "HYDROPOWER")
    assert hp["approximate_count"] == 97


def test_registry_yaml_has_fiscal_quarters():
    data = load_registry_yaml()
    fy = data["nepali_fiscal_year"]
    assert fy["fy_label"] == "2082/83"
    qs = fy["quarters"]
    assert {q["q"] for q in qs} == {1, 2, 3, 4}
