from __future__ import annotations

"""
Legacy shim.

This repository originally shipped a single-file script named `patch-kit.py`.
The published package exposes the `patch_kit` CLI entry point, implemented
in `patch_kit.cli`.

This shim lets you run the CLI from the repo root:

    python patch_kit.py --help
"""

import sys
from pathlib import Path


_repo_root = Path(__file__).resolve().parent
_src = _repo_root / "src"
if _src.exists():
    sys.path.insert(0, str(_src))

from patch_kit.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

