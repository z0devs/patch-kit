from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

from importlib.metadata import PackageNotFoundError, version

from .diffing import build_unified_diff_for_installed_dist
from .errors import (
    DistributionNotFoundError,
    OverlayApplyError,
    PatchApplyError,
    PatchLoadError,
    PatchWriteError,
)
from .fs import copy_tree_overlay, find_site_packages_dir
from .installer import download_dist_to_target
from .metadata import suggest_distributions
from .overlay import detect_and_copy_added_files
from .patch_apply import apply_patch_file
from .types import ApplyPatchItemResult, ApplyPatchesResult, CreatePatchResult


@dataclass(frozen=True)
class CreateOptions:
    patch_dir: Path = Path("patches")
    force: bool = False
    prefer_uv: bool = True


@dataclass(frozen=True)
class ApplyOptions:
    patch_dir: Path = Path("patches")


def create_patch(dist_name: str, *, options: CreateOptions | None = None) -> CreatePatchResult:
    options = options or CreateOptions()
    try:
        dist_version = version(dist_name)
    except PackageNotFoundError:
        raise DistributionNotFoundError(dist_name, suggest_distributions(dist_name))

    dist_spec = f"{dist_name}=={dist_version}"
    patch_dir = options.patch_dir
    patch_dir.mkdir(parents=True, exist_ok=True)

    patch_path = patch_dir / f"{dist_spec}.patch"
    overlay_dir = patch_dir / f"{dist_spec}.files"

    if patch_path.exists() and not options.force:
        raise PatchWriteError(
            f"Patch already exists at {patch_path}. Use --force to overwrite."
        )

    if options.force and overlay_dir.exists():
        try:
            shutil.rmtree(overlay_dir)
        except OSError as e:
            raise PatchWriteError(str(e))

    with TemporaryDirectory() as td:
        original_root = Path(td)
        download_dist_to_target(
            dist_name=dist_name,
            dist_version=dist_version,
            target_dir=original_root,
            prefer_uv=options.prefer_uv,
        )

        diff_out = build_unified_diff_for_installed_dist(
            dist_name=dist_name, original_root=original_root
        )

        added_files = 0
        try:
            site_packages = find_site_packages_dir()
            overlay_res = detect_and_copy_added_files(
                dist_name=dist_name,
                original_root=original_root,
                site_packages_dir=site_packages,
                overlay_dir=overlay_dir,
            )
            added_files = overlay_res.added_files
        except Exception:
            # Overlay is best-effort; diffs are still valuable.
            added_files = 0

        if diff_out.changed_files == 0 and added_files == 0:
            # Still write an empty patch file only if force requested? For now: don't.
            return CreatePatchResult(
                dist_name=dist_name,
                dist_version=dist_version,
                patch_path=patch_path,
                overlay_dir=overlay_dir,
                changed_files=0,
                added_files=0,
                skipped_files=diff_out.skipped_files,
            )

        try:
            patch_path.write_text(diff_out.diff_text, encoding="utf-8")
        except OSError as e:
            raise PatchWriteError(str(e))

    return CreatePatchResult(
        dist_name=dist_name,
        dist_version=dist_version,
        patch_path=patch_path,
        overlay_dir=overlay_dir,
        changed_files=diff_out.changed_files,
        added_files=added_files,
        skipped_files=diff_out.skipped_files,
    )


def apply_patches(*, options: ApplyOptions | None = None) -> ApplyPatchesResult:
    options = options or ApplyOptions()
    patch_dir = options.patch_dir
    if not patch_dir.exists():
        return ApplyPatchesResult(items=[])

    site_packages = find_site_packages_dir()
    items: list[ApplyPatchItemResult] = []

    for patch_path in sorted(patch_dir.glob("*.patch")):
        try:
            dist_name, dist_version = patch_path.stem.split("==", 1)
        except ValueError:
            items.append(
                ApplyPatchItemResult(
                    dist_name="",
                    dist_version="",
                    patch_path=patch_path,
                    overlay_dir=patch_dir / f"{patch_path.stem}.files",
                    applied=False,
                    reason="Invalid patch filename; expected <dist>==<ver>.patch",
                )
            )
            continue

        try:
            installed_version = version(dist_name)
        except PackageNotFoundError:
            items.append(
                ApplyPatchItemResult(
                    dist_name=dist_name,
                    dist_version=dist_version,
                    patch_path=patch_path,
                    overlay_dir=patch_dir / f"{patch_path.stem}.files",
                    applied=False,
                    reason="Distribution not installed",
                )
            )
            continue

        if installed_version != dist_version:
            items.append(
                ApplyPatchItemResult(
                    dist_name=dist_name,
                    dist_version=dist_version,
                    patch_path=patch_path,
                    overlay_dir=patch_dir / f"{patch_path.stem}.files",
                    applied=False,
                    reason=f"Version mismatch (installed {installed_version})",
                )
            )
            continue

        overlay_dir = patch_dir / f"{patch_path.stem}.files"
        copied = 0
        if overlay_dir.exists() and overlay_dir.is_dir():
            try:
                copied = copy_tree_overlay(overlay_dir, site_packages)
            except Exception as e:
                raise OverlayApplyError(
                    f"Failed applying overlay files for {dist_name}: {e}"
                )

        outcome = apply_patch_file(patch_path=patch_path, root=site_packages)
        if not outcome.applied:
            items.append(
                ApplyPatchItemResult(
                    dist_name=dist_name,
                    dist_version=dist_version,
                    patch_path=patch_path,
                    overlay_dir=overlay_dir,
                    applied=False,
                    reason=outcome.last_message or "Patch failed to apply",
                    overlay_files_copied=copied,
                )
            )
            continue

        items.append(
            ApplyPatchItemResult(
                dist_name=dist_name,
                dist_version=dist_version,
                patch_path=patch_path,
                overlay_dir=overlay_dir,
                applied=True,
                reason=None,
                overlay_files_copied=copied,
            )
        )

    return ApplyPatchesResult(items=items)

