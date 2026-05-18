"""NEPSE data foundation shared by all nepse-* skills.

Public surface:
    NepseClient          — abstract interface; pick a backend with `create()`
    Security             — listing record
    Ohlcv                — daily bar
    Fundamentals         — quarterly snapshot
    Registry             — universe + sector taxonomy (from config/registry.yaml)
    TradingCalendar      — session / week / holiday helpers (from config/nepse_rules.yaml)
    format_npr           — display helper
    NepseConfigError     — raised when configuration is missing or malformed
"""

from common.nepse.client import (
    Fundamentals,
    NepseClient,
    NepseConfigError,
    Ohlcv,
    Security,
)
from common.nepse.formats import format_npr
from common.nepse.registry import Registry, Sector
from common.nepse.trading_calendar import TradingCalendar

__all__ = [
    "Fundamentals",
    "NepseClient",
    "NepseConfigError",
    "Ohlcv",
    "Registry",
    "Sector",
    "Security",
    "TradingCalendar",
    "format_npr",
]
