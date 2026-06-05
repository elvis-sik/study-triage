#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent

for source in (
    WORKSPACE / "gui-agent-workbench" / "src",
    WORKSPACE / "anki-addon-workbench" / "src",
):
    if source.exists():
        sys.path.insert(0, str(source))

from anki_addon_workbench.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--config-root", str(ROOT), "smoke", *sys.argv[1:]]))
