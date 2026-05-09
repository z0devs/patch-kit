from __future__ import annotations

import site
import sys
from pathlib import Path
import shutil

from .errors import SitePackagesNotFoundError


def find_site_packages_dir() -> Path:
    """
    Best-effort site-packages discovery.

    Note: This is still heuristic; for some environments the more correct approach
    is to locate files via `importlib.metadata.distribution(...).locate_file(...)`.
    """
    for p in sys.path:
        if "site-packages" in p:
            try:
                return Path(p)
            except Exception:
                continue
    try:
        candidates = site.getsitepackages()
    except Exception:
        candidates = []
    if candidates:
        return Path(candidates[0])
    raise SitePackagesNotFoundError("Could not find site-packages directory.")


def is_safe_relative_path(p: Path) -> bool:
    if p.is_absolute():
        return False
    return ".." not in p.parts


def copy_tree_overlay(src_root: Path, dst_root: Path) -> int:
    """
    Copy all files from src_root into dst_root preserving relative paths.
    Returns count of files copied.
    """
    copied = 0
    if not src_root.exists():
        return 0
    for src in src_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(src_root)
        if not is_safe_relative_path(rel):
            raise ValueError(f"Unsafe relative path in overlay: {rel}")
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied

