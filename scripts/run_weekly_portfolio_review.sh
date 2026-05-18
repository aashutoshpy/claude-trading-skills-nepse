#!/usr/bin/env bash
# NEPSE Weekly Portfolio Review — wrapper for the Claude Desktop weekly routine.
#
# Pre-step 0/3: normalize the raw MeroShare export (data/meroshare_export.csv)
# into our tracker schema, joining with cost basis from data/cost_basis.csv.
# Then run the tracker and refresh today's snapshot.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REPORTS_DIR="${REPORTS_DIR:-reports}"
PORTFOLIO_CSV="${PORTFOLIO_CSV:-data/nepse_portfolio.csv}"
MEROSHARE_CSV="${MEROSHARE_CSV:-data/meroshare_export.csv}"
COST_BASIS_CSV="${COST_BASIS_CSV:-data/cost_basis.csv}"
mkdir -p "$REPORTS_DIR"

log() { printf '\n=== %s ===\n' "$1" >&2; }

# 0/3 — normalize MeroShare CSV → tracker schema (if user hasn't done so by hand)
if [[ -f "$MEROSHARE_CSV" ]]; then
  log "0/3  Normalizing MeroShare export → tracker schema"
  set +e
  python3 scripts/normalize_meroshare_csv.py \
    --meroshare-csv "$MEROSHARE_CSV" \
    --cost-basis-csv "$COST_BASIS_CSV" \
    --output "$PORTFOLIO_CSV"
  NORMALIZE_RC=$?
  set -e
  if [[ $NORMALIZE_RC -eq 1 ]]; then
    printf '\nFATAL: normalizer failed (exit 1) — cannot proceed.\n' >&2
    exit 1
  fi
  # exit 3 (partial — some cost basis missing) is non-fatal; tracker will fail
  # gracefully on rows with blank avg_cost. Continue.
fi

if [[ ! -f "$PORTFOLIO_CSV" ]]; then
  cat >&2 <<EOF
ERROR: portfolio CSV not found at $PORTFOLIO_CSV

To populate it:
  1. Log into meroshare.cdsc.com.np
  2. My Portfolio → Export
  3. Save the raw export as $MEROSHARE_CSV
  4. Copy data/cost_basis.csv.example to $COST_BASIS_CSV and fill in cost basis
  5. Re-run this script — the normalizer in step 0/3 will produce $PORTFOLIO_CSV

Skipping weekly review.
EOF
  exit 2
fi

log "1/3  Refreshing today's snapshot so positions are mark-to-market"
python3 scripts/fetch_nepse_snapshot.py

log "2/3  Portfolio tracker (P&L, sector concentration, margin warnings)"
if ! python3 skills/nepse-portfolio-tracker/scripts/track_portfolio.py \
    --portfolio-csv "$PORTFOLIO_CSV" --output-dir "$REPORTS_DIR"; then
  printf '\nTracker exited non-zero. Likely cause: rows in %s have blank\n' "$PORTFOLIO_CSV" >&2
  printf 'avg_cost. Fix by populating %s and re-running.\n' "$COST_BASIS_CSV" >&2
  exit 1
fi

log "3/3  Done. Reports in $REPORTS_DIR/"
ls -lt "$REPORTS_DIR"/nepse_portfolio_*.{md,json} 2>/dev/null | head -4 >&2 || true
