from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CreatePatchResult:
    dist_name: str
    dist_version: str
    patch_path: Path
    overlay_dir: Path
    changed_files: int
    added_files: int
    skipped_files: int

    @property
    def wrote_anything(self) -> bool:
        return (self.changed_files > 0) or (self.added_files > 0)


@dataclass(frozen=True)
class ApplyPatchItemResult:
    dist_name: str
    dist_version: str
    patch_path: Path
    overlay_dir: Path
    applied: bool
    reason: str | None = None
    overlay_files_copied: int = 0


@dataclass(frozen=True)
class ApplyPatchesResult:
    items: list[ApplyPatchItemResult]

    @property
    def applied_count(self) -> int:
        return sum(1 for i in self.items if i.applied)

    @property
    def skipped_count(self) -> int:
        return sum(1 for i in self.items if not i.applied)

