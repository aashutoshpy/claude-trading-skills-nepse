"""Tests for the NepseClient facade + factory."""


import pytest

from common.nepse.client import NepseClient, NepseConfigError


def test_create_default_picks_csv_backend(monkeypatch):
    """Default is `csv` since live-fetch backends are dead — see README Limitations."""
    monkeypatch.delenv("NEPSE_BACKEND", raising=False)
    client = NepseClient.create()
    assert client.backend_name == "csv"


def test_create_via_env_var(monkeypatch):
    monkeypatch.setenv("NEPSE_BACKEND", "nepalstock")
    client = NepseClient.create()
    assert client.backend_name == "nepalstock"


def test_create_explicit_backend_wins_over_env(monkeypatch):
    monkeypatch.setenv("NEPSE_BACKEND", "community")
    # Explicit arg should win — even though community backend would fail
    # to construct without a library installed.
    client = NepseClient.create(backend="nepalstock")
    assert client.backend_name == "nepalstock"


def test_unknown_backend_raises():
    with pytest.raises(NepseConfigError):
        NepseClient.create(backend="not-a-real-backend")


def test_community_backend_raises_when_no_library_installed():
    # The community library wrapper raises ImportError if no candidate
    # library is installed in the test env. We just verify the path
    # routes to that backend correctly (and the import error is clear).
    import importlib
    have_any = False
    for mod in ("nepse_api", "Nepse"):
        try:
            importlib.import_module(mod)
            have_any = True
            break
        except ImportError:
            continue
    if have_any:
        pytest.skip("A community NEPSE library is installed; can't test the no-library path")
    with pytest.raises(ImportError):
        NepseClient.create(backend="community")
