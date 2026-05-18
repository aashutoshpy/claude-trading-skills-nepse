"""Tests for the NEPSE_INSECURE_TLS opt-in.

The default `nepalstock.com.np` backend can fail with
`CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate` when the
server presents an incomplete TLS chain. NEPSE_INSECURE_TLS=1 is a documented
escape hatch that disables verification — with a loud stderr warning.
"""

from common.nepse.backends._http import HttpClient
from common.nepse.backends.nepalstock_scraper import NepalstockScraperBackend


def test_http_client_defaults_to_verify_true():
    c = HttpClient()
    assert c.session.verify is True


def test_http_client_honors_verify_false():
    c = HttpClient(verify=False)
    assert c.session.verify is False


def test_backend_uses_verify_true_when_env_unset(monkeypatch):
    monkeypatch.delenv("NEPSE_INSECURE_TLS", raising=False)
    b = NepalstockScraperBackend()
    assert b.http.session.verify is True


def test_backend_uses_verify_false_when_env_truthy(monkeypatch, capsys):
    monkeypatch.setenv("NEPSE_INSECURE_TLS", "1")
    b = NepalstockScraperBackend()
    assert b.http.session.verify is False
    err = capsys.readouterr().err
    assert "NEPSE_INSECURE_TLS" in err
    assert "disabling TLS verification" in err
    assert "MITM" in err  # warning should mention the trade-off


def test_backend_accepts_alternative_truthy_values(monkeypatch):
    for val in ("true", "yes", "y", "on", "TRUE"):
        monkeypatch.setenv("NEPSE_INSECURE_TLS", val)
        b = NepalstockScraperBackend()
        assert b.http.session.verify is False, f"value {val!r} should disable verify"


def test_backend_keeps_verify_for_unrecognized_values(monkeypatch):
    for val in ("0", "false", "no", "", "  ", "maybe"):
        monkeypatch.setenv("NEPSE_INSECURE_TLS", val)
        b = NepalstockScraperBackend()
        assert b.http.session.verify is True, f"value {val!r} should NOT disable verify"


def test_explicit_http_overrides_env(monkeypatch):
    """An explicitly-passed HttpClient takes precedence over the env flag."""
    monkeypatch.setenv("NEPSE_INSECURE_TLS", "1")
    explicit = HttpClient(verify=True)
    b = NepalstockScraperBackend(http=explicit)
    # No warning emitted because the env-driven path wasn't taken.
    assert b.http is explicit
    assert b.http.session.verify is True
