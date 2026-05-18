"""Locate and load the NEPSE YAML config files.

Resolves config paths from the repo root regardless of where a script
is invoked. NEPSE_CONFIG_DIR overrides the default `config/` location
(useful for tests with synthetic fixtures).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


class NepseConfigError(RuntimeError):
    """Raised when a NEPSE config file is missing or malformed."""


def _repo_root() -> Path:
    # common/nepse/_config.py → parents[2] is the repo root.
    return Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    override = os.environ.get("NEPSE_CONFIG_DIR")
    if override:
        return Path(override)
    return _repo_root() / "config"


def _load_yaml(name: str) -> dict[str, Any]:
    path = config_dir() / name
    if not path.exists():
        raise NepseConfigError(f"NEPSE config file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise NepseConfigError(f"Could not parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise NepseConfigError(f"{path}: top level must be a mapping, got {type(data).__name__}")
    return data


@lru_cache(maxsize=2)
def load_rules() -> dict[str, Any]:
    """Load `nepse_rules.yaml` (cached)."""
    return _load_yaml("nepse_rules.yaml")


@lru_cache(maxsize=2)
def load_registry_yaml() -> dict[str, Any]:
    """Load `registry.yaml` (cached)."""
    return _load_yaml("registry.yaml")


def reset_cache() -> None:
    """Reset the lru_cache — used by tests that point NEPSE_CONFIG_DIR at fixtures."""
    load_rules.cache_clear()
    load_registry_yaml.cache_clear()
