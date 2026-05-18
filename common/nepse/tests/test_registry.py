"""Tests for the NEPSE sector + universe registry."""

import pytest

from common.nepse._config import reset_cache
from common.nepse.registry import Registry


@pytest.fixture(autouse=True)
def _reset():
    reset_cache()
    yield
    reset_cache()


def test_registry_loads_thirteen_sectors():
    r = Registry.load()
    assert len(r.sectors) == 13


def test_sector_by_id_returns_hydropower_as_largest():
    r = Registry.load()
    hp = r.sector_by_id("HYDROPOWER")
    assert hp.display_name == "Hydropower"
    assert hp.approximate_count == 97


def test_sector_by_id_raises_on_unknown():
    r = Registry.load()
    with pytest.raises(KeyError):
        r.sector_by_id("FAKE_SECTOR")


def test_fiscal_year_label_is_current_nepali_FY():
    r = Registry.load()
    assert r.fiscal_year_label == "2082/83"
    assert len(r.fiscal_quarter_ends) == 4


def test_margin_eligibility_is_empty_until_refresh():
    # The seed YAML ships with empty list; refresh script populates it.
    r = Registry.load()
    assert r.is_margin_eligible("NABIL") is False
