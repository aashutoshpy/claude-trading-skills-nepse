"""CSV-file backend — read NEPSE OHLCV from local CSVs.

Why this backend exists:
- `nepalstock.com.np` rejects direct API calls (TLS chain + 401 anti-bot).
- `nepse-api 1.x` (the only community Python lib) depends on services
  that are no longer running.
- Sharesansar and merolagani actively block scraping (silent 202 responses).

But every Nepali trader can download OHLCV CSVs manually — sharesansar's
"Today's Price" page has an Excel-export button, merolagani exposes
per-company CSVs, and many traders maintain Google Sheets. This backend
reads from local files and is therefore fully reliable and offline.

Layout (default; override via `data_dir` or `NEPSE_CSV_DATA_DIR`):

    data/
      ohlcv/
        NABIL.csv         # one file per symbol, headered
        UPPER.csv
        ...
      constituents.csv    # optional — see _load_constituents()
      indexes/
        NEPSE.csv         # index OHLCV
        BANKING.csv
        ...

CSV schema for `ohlcv/<SYMBOL>.csv` and `indexes/<INDEX>.csv`:

    date,open,high,low,close,volume
    2026-05-17,1180.00,1212.00,1175.00,1207.50,84320
    2026-05-16,1195.00,1208.00,1182.00,1180.00,52110
    ...

Order is irrelevant — the backend sorts ascending by date.
"""

from __future__ import annotations

import csv
import os
from datetime import date
from pathlib import Path

from common.nepse.client import Fundamentals, Ohlcv, Security
from common.nepse.registry import Registry

_DEFAULT_DATA_DIR_ENV = "NEPSE_CSV_DATA_DIR"
_DEFAULT_DATA_DIR = "data"


class CsvFileBackend:
    """Reads OHLCV + universe from local CSV files. No network."""

    name = "csv"

    def __init__(self, *, data_dir: str | os.PathLike[str] | None = None):
        if data_dir is None:
            data_dir = os.environ.get(_DEFAULT_DATA_DIR_ENV, _DEFAULT_DATA_DIR)
        self.data_dir = Path(data_dir).expanduser().resolve()
        try:
            self._registry: Registry | None = Registry.load()
        except Exception:
            self._registry = None

    # ---- universe ---------------------------------------------------------

    def list_constituents(self) -> list[Security]:
        """Read constituents from <data_dir>/constituents.csv.

        Schema (header row required):
            symbol,name,sector_id[,margin_eligible]

        If the file is absent, fall back to discovering symbols from any
        `ohlcv/<SYMBOL>.csv` files present, and the optional watchlist
        `nepse_starter_watchlist.txt`.
        """
        path = self.data_dir / "constituents.csv"
        margin_set = (
            self._registry.margin_eligible_symbols if self._registry else frozenset()
        )

        if path.exists():
            out: list[Security] = []
            with path.open(newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    symbol = (row.get("symbol") or "").strip().upper()
                    if not symbol:
                        continue
                    out.append(
                        Security(
                            symbol=symbol,
                            name=(row.get("name") or symbol).strip(),
                            sector_id=(row.get("sector_id") or "OTHERS").strip(),
                            listed=True,
                            margin_eligible=(
                                _truthy(row.get("margin_eligible"))
                                or symbol in margin_set
                            ),
                        )
                    )
            return out

        # Fallback A: discover from ohlcv/<SYMBOL>.csv files
        ohlcv_dir = self.data_dir / "ohlcv"
        discovered: set[str] = set()
        if ohlcv_dir.exists():
            for p in ohlcv_dir.glob("*.csv"):
                discovered.add(p.stem.upper())

        # Fallback B: starter watchlist (a plaintext file shipped at the
        # data/ root by the trader-onboarding workflow).
        watchlist = self.data_dir / "nepse_starter_watchlist.txt"
        if watchlist.exists():
            for line in watchlist.read_text(encoding="utf-8").splitlines():
                sym = line.strip().upper()
                if sym and not sym.startswith("#"):
                    discovered.add(sym)

        return [
            Security(
                symbol=s,
                name=s,
                sector_id="OTHERS",
                listed=True,
                margin_eligible=(s in margin_set),
            )
            for s in sorted(discovered)
        ]

    # ---- OHLCV -----------------------------------------------------------

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[Ohlcv]:
        path = self.data_dir / "ohlcv" / f"{symbol.upper()}.csv"
        return _read_ohlcv_csv(path, start, end)

    def get_index(self, index_name: str, start: date, end: date) -> list[Ohlcv]:
        path = self.data_dir / "indexes" / f"{index_name.upper()}.csv"
        return _read_ohlcv_csv(path, start, end)

    def get_quote(self, symbol: str) -> Ohlcv | None:
        # Latest bar from the OHLCV CSV.
        path = self.data_dir / "ohlcv" / f"{symbol.upper()}.csv"
        bars = _read_ohlcv_csv(path, date.min, date.max)
        return bars[-1] if bars else None

    # ---- not supported (intentional) -------------------------------------

    def get_floorsheet(self, day: date) -> list[dict] | None:
        # No public CSV source ships floorsheet; users can drop one in if needed.
        path = self.data_dir / "floorsheet" / f"{day.isoformat()}.csv"
        if not path.exists():
            return None
        with path.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def get_fundamentals(self, symbol: str) -> Fundamentals | None:
        # Skills that need fundamentals already accept user-maintained CSVs
        # via their own --fundamentals-csv flag; we don't try to enrich here.
        return None


# ---- helpers --------------------------------------------------------------


def _read_ohlcv_csv(path: Path, start: date, end: date) -> list[Ohlcv]:
    """Read a date,open,high,low,close,volume[,prev_close] CSV.

    Tolerates extra columns, mixed case headers, blank rows, and unsorted dates.
    Filters to bars in [start, end]. Returns ascending by date.
    """
    if not path.exists():
        return []
    bars: list[Ohlcv] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            return []
        # Normalize header lookups (case-insensitive)
        keymap = {k.lower(): k for k in reader.fieldnames if k}
        for row in reader:
            raw_date = (row.get(keymap.get("date", ""), "") or "").strip()
            if not raw_date:
                continue
            try:
                d = date.fromisoformat(raw_date[:10])
            except ValueError:
                continue
            if d < start or d > end:
                continue
            try:
                bar = Ohlcv(
                    day=d,
                    open=float(row[keymap["open"]]),
                    high=float(row[keymap["high"]]),
                    low=float(row[keymap["low"]]),
                    close=float(row[keymap["close"]]),
                    volume=int(float(row.get(keymap.get("volume", ""), 0) or 0)),
                    prev_close=(
                        float(row[keymap["prev_close"]])
                        if "prev_close" in keymap and row.get(keymap["prev_close"])
                        else None
                    ),
                )
            except (KeyError, ValueError):
                continue
            bars.append(bar)
    bars.sort(key=lambda b: b.day)
    return bars


def _truthy(s: str | None) -> bool:
    return (s or "").strip().lower() in {"1", "true", "yes", "y", "on"}
