"""Make `common.nepse` importable when scripts are run directly.

NEPSE skills depend on `common.nepse.*`. Importing this module at the
top of every CLI / test file inserts the repo root onto sys.path so the
import succeeds regardless of cwd.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
