from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from importlib.metadata import distribution
from pathlib import Path


@dataclass(frozen=True)
class DiffOutput:
    diff_text: str
    changed_files: int
    skipped_files: int


def build_unified_diff_for_installed_dist(
    *,
    dist_name: str,
    original_root: Path,
    encoding: str = "utf-8",
) -> DiffOutput:
    """
    Compare installed distribution files against an "original" copy rooted at original_root.

    - Only diffs text files (best-effort by decoding with `encoding`)
    - Skips `.dist-info` and `.pyc`
    """
    dist = distribution(dist_name)

    out = []
    changed = 0
    skipped = 0

    for rel in dist.files or []:
        # `rel` is a PackagePath (path-like, relative)
        rel_path = Path(str(rel))
        if rel_path.parent.suffix == ".dist-info":
            continue
        if rel_path.suffix == ".pyc":
            continue

        installed_path = Path(dist.locate_file(rel))
        original_path = original_root / rel_path
        if not installed_path.exists() or not original_path.exists():
            continue

        try:
            installed_lines = installed_path.read_text(encoding=encoding).splitlines(True)
            original_lines = original_path.read_text(encoding=encoding).splitlines(True)
        except (UnicodeDecodeError, UnicodeError):
            skipped += 1
            continue
        except OSError:
            skipped += 1
            continue

        diff = list(
            unified_diff(
                original_lines,
                installed_lines,
                fromfile=str(rel_path),
                tofile=str(rel_path),
            )
        )
        if diff:
            changed += 1
            out.append("".join(diff))

    return DiffOutput(diff_text="".join(out), changed_files=changed, skipped_files=skipped)

