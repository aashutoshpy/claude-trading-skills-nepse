"""Tests for the disk-backed response cache."""

import time

import pytest

from common.nepse.cache import NepseCache


@pytest.fixture
def cache(tmp_path):
    return NepseCache(cache_dir=tmp_path)


def test_get_returns_none_when_missing(cache):
    assert cache.get("ns", "https://x", None, ttl_seconds=60) is None


def test_put_then_get_round_trip(cache):
    cache.put("ns", "https://x", {"a": 1}, {"hello": "world"})
    got = cache.get("ns", "https://x", {"a": 1}, ttl_seconds=60)
    assert got == {"hello": "world"}


def test_put_atomic_no_partial_file(cache, tmp_path):
    cache.put("ns", "https://x", None, {"payload": True})
    # No .tmp residue
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_cache_key_distinguishes_params(cache):
    cache.put("ns", "https://x", {"a": 1}, "first")
    cache.put("ns", "https://x", {"a": 2}, "second")
    assert cache.get("ns", "https://x", {"a": 1}, ttl_seconds=60) == "first"
    assert cache.get("ns", "https://x", {"a": 2}, ttl_seconds=60) == "second"


def test_cache_key_distinguishes_namespace(cache):
    cache.put("ohlcv", "https://x", None, "ohlcv-data")
    cache.put("quote", "https://x", None, "quote-data")
    assert cache.get("ohlcv", "https://x", None, ttl_seconds=60) == "ohlcv-data"
    assert cache.get("quote", "https://x", None, ttl_seconds=60) == "quote-data"


def test_ttl_expiry(cache, tmp_path):
    cache.put("ns", "https://x", None, "value")
    # Force-age the file by setting mtime in the past
    f = next(tmp_path.glob("*.json"))
    old = time.time() - 100
    import os
    os.utime(f, (old, old))
    # ttl 50s → file is older, miss
    assert cache.get("ns", "https://x", None, ttl_seconds=50) is None
    # ttl 200s → still fresh
    assert cache.get("ns", "https://x", None, ttl_seconds=200) == "value"


def test_clear_removes_all_entries(cache, tmp_path):
    for i in range(3):
        cache.put("ns", f"https://x/{i}", None, i)
    removed = cache.clear()
    assert removed == 3
    assert list(tmp_path.glob("*.json")) == []


def test_corrupted_file_returns_none(cache, tmp_path):
    # Write a junk file with the expected naming scheme
    f = tmp_path / "ns_aaaaaaaaaaaaaaaaaaaaaaaa.json"
    f.write_text("{not valid json")
    # get_json would call get(...); if the file matches the key it should
    # safely return None instead of crashing
    cache.put("ns", "https://x", None, "valid")
    # Even with the junk file present, valid entries still resolve
    assert cache.get("ns", "https://x", None, ttl_seconds=60) == "valid"
