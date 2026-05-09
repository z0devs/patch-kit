from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import distribution
from pathlib import Path
import shutil

from .fs import is_safe_relative_path


@dataclass(frozen=True)
class OverlayDetectionResult:
    overlay_dir: Path
    added_files: int


def detect_and_copy_added_files(
    *,
    dist_name: str,
    original_root: Path,
    site_packages_dir: Path,
    overlay_dir: Path,
) -> OverlayDetectionResult:
    """
    Detect "new" files that exist in the installed environment but do not exist
    in the downloaded original copy.

    We avoid assuming a single top-level package dir. Instead, we compute a set
    of top-level roots present in the distribution file list and scan those.
    """
    dist = distribution(dist_name)

    roots: set[str] = set()
    for rel in dist.files or []:
        rel_path = Path(str(rel))
        if rel_path.parent.suffix == ".dist-info":
            continue
        if not rel_path.parts:
            continue
        roots.add(rel_path.parts[0])

    added = 0
    overlay_dir.mkdir(parents=True, exist_ok=True)

    for root in sorted(roots):
        candidate_root = site_packages_dir / root
        if not candidate_root.exists():
            continue
        for src in candidate_root.rglob("*"):
            if not src.is_file():
                continue
            if "__pycache__" in src.parts or src.suffix == ".pyc":
                continue

            rel_to_site = src.relative_to(site_packages_dir)
            if not is_safe_relative_path(rel_to_site):
                raise ValueError(f"Unsafe added file path: {rel_to_site}")

            if not (original_root / rel_to_site).exists():
                dst = overlay_dir / rel_to_site
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                added += 1

    return OverlayDetectionResult(overlay_dir=overlay_dir, added_files=added)

