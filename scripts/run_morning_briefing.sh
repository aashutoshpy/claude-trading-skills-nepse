#!/usr/bin/env bash
# NEPSE Morning Briefing — wrapper used by the Claude Desktop daily routine.
#
# Runs the data-fetching + regime + screener pipeline in order. Each step
# exits non-zero on failure and the wrapper propagates that (set -e).
# Intended to be called by docs/routines/daily-morning-briefing.md, but
# safe to run by hand too.
#
# Outputs land in reports/. The routine's Claude turn reads them and
# writes reports/morning_briefing_YYYY-MM-DD.md as the final synthesis.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REPORTS_DIR="${REPORTS_DIR:-reports}"
mkdir -p "$REPORTS_DIR"

log() { printf '\n=== %s ===\n' "$1" >&2; }

# Track step failures without aborting — we want partial reports even when
# one analyzer needs data we don't have cached (e.g. sector indices).
FAILURES=()
run_step() {
  local label="$1"; shift
  log "$label"
  if ! "$@"; then
    FAILURES+=("$label")
    printf '  [step failed; continuing — final summary will flag this]\n' >&2
  fi
}

# Fetcher first — if this fails (network down), the rest is hopeless;
# fail the whole wrapper. The remaining steps are non-fatal.
log "1/5  Refreshing OHLCV (today's snapshot from sharesansar)"
if ! python3 scripts/fetch_nepse_snapshot.py; then
  printf '\nFATAL: fetcher failed; cannot continue (downstream steps depend on fresh OHLCV).\n' >&2
  exit 1
fi

run_step "2/5  Market breadth (advances/declines, % above 50/200 SMA, regime)" \
  python3 skills/nepse-market-breadth-analyzer/scripts/compute_nepse_breadth.py \
    --output-dir "$REPORTS_DIR"

run_step "3/5  Uptrend ratio (% of names above 200-SMA + 20-day trajectory)" \
  python3 skills/nepse-uptrend-analyzer/scripts/compute_uptrend_ratio.py \
    --output-dir "$REPORTS_DIR"

run_step "4/5  Sector ranking (13 NEPSE sector indices)" \
  python3 skills/nepse-sector-analyst/scripts/rank_nepse_sectors.py \
    --output-dir "$REPORTS_DIR"

run_step "5/5  VCP screener (candidate base structures + actionable scores)" \
  python3 skills/nepse-vcp-screener/scripts/screen_nepse_vcp.py \
    --output-dir "$REPORTS_DIR"

log "Done. Reports written to $REPORTS_DIR/"
ls -lt "$REPORTS_DIR"/*"$(date +%F)"* 2>/dev/null | head -8 >&2 || true

if [[ "${#FAILURES[@]}" -gt 0 ]]; then
  printf '\nNOTE: %d step(s) failed but the briefing continues:\n' "${#FAILURES[@]}" >&2
  for f in "${FAILURES[@]}"; do printf '  - %s\n' "$f" >&2; done
  printf '\nMost common cause: the analyzer needs data not in your CSV cache\n' >&2
  printf '(e.g. sector indices). The Claude routine will note this gap in the\n' >&2
  printf 'briefing and proceed with whatever signals DID materialize.\n' >&2
fi
exit 0
