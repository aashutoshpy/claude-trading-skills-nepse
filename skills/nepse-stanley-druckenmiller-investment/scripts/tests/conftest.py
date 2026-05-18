"""Make `common.nepse` and sibling scripts importable in tests."""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_SCRIPTS_DIR = _HERE.parents[1]
_REPO_ROOT = _HERE.parents[4]

for p in (_REPO_ROOT, _SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
