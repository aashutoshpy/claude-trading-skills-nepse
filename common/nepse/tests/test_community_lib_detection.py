"""Tests for community-lib import detection.

`pip install nepse-api` installs as top-level module `nepse` (not `nepse_api`).
We try `nepse` first, then `nepse_api`, then `Nepse`. When nothing imports we
return diagnostics that the user (or an LLM helper) can act on.
"""

import sys
import types

import pytest

from common.nepse.backends.community_lib import CommunityLibBackend


@pytest.fixture
def _no_nepse_modules():
    """Snapshot + remove any pre-existing nepse-related modules around a test."""
    backup = {}
    for name in ("nepse", "nepse_api", "Nepse"):
        if name in sys.modules:
            backup[name] = sys.modules[name]
            del sys.modules[name]
    yield
    for name in ("nepse", "nepse_api", "Nepse"):
        sys.modules.pop(name, None)
    sys.modules.update(backup)


def test_detection_prefers_nepse_module(_no_nepse_modules):
    fake = types.ModuleType("nepse")
    fake.__file__ = "<test>"
    sys.modules["nepse"] = fake

    impl, diag = CommunityLibBackend._import_first_available()
    assert impl is fake
    assert any("import nepse: OK" in d for d in diag)


def test_detection_falls_back_to_nepse_api(_no_nepse_modules):
    fake = types.ModuleType("nepse_api")
    fake.__file__ = "<test>"
    sys.modules["nepse_api"] = fake

    impl, diag = CommunityLibBackend._import_first_available()
    assert impl is fake
    assert any("import nepse_api: OK" in d for d in diag)


def test_detection_captures_cgi_missing_error_clearly(_no_nepse_modules, monkeypatch):
    """Python 3.13+ removed `cgi`; the `nepse` PyPI lib still imports it.
    The error must surface clearly in diagnostics, not get swallowed.
    """
    builtin_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __import__

    def fake_import(name, *args, **kwargs):
        if name == "nepse":
            raise ModuleNotFoundError("No module named 'cgi'")
        return builtin_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    impl, diag = CommunityLibBackend._import_first_available()
    assert impl is None
    nepse_diag = [d for d in diag if d.startswith("import nepse:")]
    assert nepse_diag, f"expected diag for `import nepse`, got {diag}"
    assert "cgi" in nepse_diag[0]


def test_init_raises_with_actionable_message_when_nothing_imports(_no_nepse_modules, monkeypatch):
    builtin_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __import__

    def fake_import(name, *args, **kwargs):
        if name in ("nepse", "nepse_api", "Nepse"):
            raise ImportError(f"No module named {name!r}")
        return builtin_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(ImportError) as exc_info:
        CommunityLibBackend()
    msg = str(exc_info.value)
    assert "pip install nepse-api" in msg
    assert "legacy-cgi" in msg  # mention the Python 3.13+ workaround
    assert "NEPSE_INSECURE_TLS" in msg  # point to the alternative path
