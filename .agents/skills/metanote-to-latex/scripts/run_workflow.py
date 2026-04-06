#!/usr/bin/env python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[4]
    tool = root / "tools" / "metanote_to_tex.py"
    command = [sys.executable, str(tool), *(argv or sys.argv[1:])]
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
