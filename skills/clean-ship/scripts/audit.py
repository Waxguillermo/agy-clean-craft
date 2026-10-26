"""Black-box repository hygiene audit script for the /clean-ship skill."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agy_clean_craft.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["audit", *sys.argv[1:]]))
