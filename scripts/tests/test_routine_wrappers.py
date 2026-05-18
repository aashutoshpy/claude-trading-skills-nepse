"""Tests for the Claude Desktop routine wrapper shell scripts.

These tests stub out the underlying Python scripts via PATH shimming so
they don't hit network or actually read the OHLCV cache. We verify:

- The wrapper invokes the expected sub-scripts in order
- Exit-code propagation matches the design (fetcher failure → fail;
  non-fatal step failure → continue, exit 0, report in stderr)
- The portfolio wrapper bails clearly when its CSV input is missing
"""

import os
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


@pytest.fixture
def fake_python3(tmp_path: Path, monkeypatch):
    """Replace python3 on PATH with a fake that records its argv to a file.

    Behavior is controlled via env vars:
      FAKE_FAIL_ON: substring of argv[0] that should cause exit 1
      FAKE_LOG_FILE: path where each invocation appends its argv (newline-separated)
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "calls.log"
    log_file.touch()  # pre-create so read_text() works even with zero invocations

    # Shim 'python3' with a shell script that logs and optionally fails.
    shim = bin_dir / "python3"
    shim.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "$@" >> {log_file}
        # Some sub-scripts produce report files for the wrapper's `ls` step.
        # Tolerate the wrapper's later steps by always exiting 0 unless the
        # caller asks us to fail on a specific argv match.
        if [[ -n "${{FAKE_FAIL_ON:-}}" ]] && [[ "$*" == *"$FAKE_FAIL_ON"* ]]; then
            echo "ERROR (faked): step matched $FAKE_FAIL_ON" >&2
            exit 1
        fi
        exit 0
    """))
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG_FILE", str(log_file))
    return log_file


def _run_wrapper(name: str, tmp_path: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run a wrapper in an isolated working dir that mirrors the repo layout."""
    # Copy just enough of the repo into tmp_path to make the wrapper happy.
    work = tmp_path / "work"
    work.mkdir()
    shutil.copy2(SCRIPTS / name, work / name)
    (work / name).chmod(0o755)
    # Wrappers cd to REPO_ROOT via `dirname $BASH_SOURCE/..`, so we need
    # a `scripts/` directory + a `reports/` parent dir.
    (work / "reports").mkdir()
    (work / "data").mkdir()

    # Move our shim'd script into a `scripts/` subdir so the wrapper's
    # `cd "$(dirname ...)/.."` lands at `work/`.
    scripts_dir = work / "scripts"
    scripts_dir.mkdir()
    (work / name).rename(scripts_dir / name)

    full_env = {**os.environ, **(env or {})}
    return subprocess.run(
        ["bash", str(scripts_dir / name)],
        capture_output=True, text=True, env=full_env, cwd=str(work),
    )


# ---- morning_briefing ------------------------------------------------------


def test_morning_briefing_invokes_all_five_steps(fake_python3, tmp_path):
    result = _run_wrapper("run_morning_briefing.sh", tmp_path)
    assert result.returncode == 0, result.stderr
    log = fake_python3.read_text()
    assert "fetch_nepse_snapshot.py" in log
    assert "compute_nepse_breadth.py" in log
    assert "compute_uptrend_ratio.py" in log
    assert "rank_nepse_sectors.py" in log
    assert "screen_nepse_vcp.py" in log


def test_morning_briefing_fetcher_failure_is_fatal(fake_python3, tmp_path):
    result = _run_wrapper(
        "run_morning_briefing.sh", tmp_path,
        env={"FAKE_FAIL_ON": "fetch_nepse_snapshot.py"},
    )
    assert result.returncode != 0  # fetcher failure must propagate
    # Subsequent steps should NOT have been invoked
    log = fake_python3.read_text()
    assert "compute_nepse_breadth.py" not in log


def test_morning_briefing_non_fatal_step_failure_continues(fake_python3, tmp_path):
    """If breadth (or any non-fetcher) step fails, the wrapper continues
    through the rest and exits 0 with a stderr summary of failures."""
    result = _run_wrapper(
        "run_morning_briefing.sh", tmp_path,
        env={"FAKE_FAIL_ON": "compute_nepse_breadth.py"},
    )
    assert result.returncode == 0, result.stderr
    log = fake_python3.read_text()
    # Later steps still ran
    assert "screen_nepse_vcp.py" in log
    # And the failure was reported in stderr
    assert "step failed" in result.stderr.lower() or "1 step(s) failed" in result.stderr


# ---- weekly_portfolio_review -----------------------------------------------


def test_weekly_review_bails_when_portfolio_csv_missing(fake_python3, tmp_path):
    result = _run_wrapper("run_weekly_portfolio_review.sh", tmp_path)
    assert result.returncode == 2, result.stderr
    assert "portfolio CSV not found" in result.stderr
    # The Python wrapper should NOT have been invoked
    log = fake_python3.read_text()
    assert "track_portfolio.py" not in log


def test_weekly_review_runs_tracker_when_csv_present(fake_python3, tmp_path):
    # Drop a fake portfolio CSV and re-test
    result = _run_wrapper(
        "run_weekly_portfolio_review.sh", tmp_path,
        env={"PORTFOLIO_CSV": "data/dummy.csv"},
    )
    # Need to ALSO have the CSV exist where the wrapper looks. Easier: stub the
    # csv path to a real file before the wrapper checks it.
    work = tmp_path / "work"
    (work / "data" / "dummy.csv").write_text("symbol,shares,avg_cost\nNABIL,10,500\n")
    result = subprocess.run(
        ["bash", str(work / "scripts" / "run_weekly_portfolio_review.sh")],
        capture_output=True, text=True, cwd=str(work),
        env={**os.environ, "PORTFOLIO_CSV": "data/dummy.csv"},
    )
    assert result.returncode == 0, result.stderr
    log = fake_python3.read_text()
    assert "track_portfolio.py" in log
    assert "fetch_nepse_snapshot.py" in log


# ---- quarterly_review ------------------------------------------------------


def test_quarterly_review_invokes_calendar_and_analyzer(fake_python3, tmp_path):
    result = _run_wrapper("run_quarterly_review.sh", tmp_path)
    assert result.returncode == 0, result.stderr
    log = fake_python3.read_text()
    assert "generate_calendar.py" in log
    assert "analyze_earnings.py" in log


def test_quarterly_review_tolerates_per_ticker_failures(fake_python3, tmp_path):
    """The analyzer is called per-ticker; some may fail (pre-filing, no data).
    The wrapper redirects 2>/dev/null and emits 'skipped' but keeps going."""
    result = _run_wrapper(
        "run_quarterly_review.sh", tmp_path,
        env={"FAKE_FAIL_ON": "analyze_earnings.py"},
    )
    assert result.returncode == 0, result.stderr
    assert "skipped" in result.stderr.lower()
