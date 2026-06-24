#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from anki_addon_workbench.cli import main


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    raise SystemExit(main(["--config-root", str(ROOT), "launch", *sys.argv[1:]]))
