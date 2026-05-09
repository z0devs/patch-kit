from __future__ import annotations

import argparse
import sys
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version

from .core import ApplyOptions, CreateOptions, apply_patches, create_patch
from .errors import PatchKitError
from .metadata import iter_installed_distributions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patch_kit",
        description="Create and apply local patches to installed Python distributions.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a patch for an installed distribution")
    p_create.add_argument("dist_name", help="Distribution name (what you pip installed)")
    p_create.add_argument(
        "--patch-dir",
        default="patches",
        help="Directory to write patch files into (default: patches)",
    )
    p_create.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing patch file if it exists",
    )
    p_create.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt before overwriting (useful for CI)",
    )
    p_create.add_argument(
        "--no-uv",
        action="store_true",
        help="Do not try uv; use pip only",
    )

    p_apply = sub.add_parser("apply", help="Apply patches found in patch-dir")
    p_apply.add_argument(
        "--patch-dir",
        default="patches",
        help="Directory to read patch files from (default: patches)",
    )

    p_list = sub.add_parser(
        "list",
        aliases=["packages"],
        help="List installed distributions for the active Python",
    )
    p_list.add_argument(
        "--versions",
        action="store_true",
        help="Include installed version per line (name==version, matches patch filenames)",
    )
    p_list.add_argument(
        "--contains",
        metavar="TEXT",
        help="Case-insensitive substring filter on distribution name",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)

    try:
        if ns.command == "create":
            patch_dir = Path(ns.patch_dir)
            force = bool(ns.force)

            if (not force) and (not bool(ns.no_prompt)) and sys.stdin.isatty():
                try:
                    dist_version = version(ns.dist_name)
                    dist_spec = f"{ns.dist_name}=={dist_version}"
                    patch_path = patch_dir / f"{dist_spec}.patch"
                    if patch_path.exists():
                        answer = input(f"Patch exists at {patch_path}. Overwrite? [y/N]: ").strip().lower()
                        if answer in {"y", "yes"}:
                            force = True
                except PackageNotFoundError:
                    # If the dist isn't installed, create_patch will raise a helpful error.
                    pass

            res = create_patch(
                ns.dist_name,
                options=CreateOptions(
                    patch_dir=patch_dir,
                    force=force,
                    prefer_uv=not bool(ns.no_uv),
                ),
            )
            if not res.wrote_anything:
                print("No changes detected. No patch created.")
                return 0
            print(f"Wrote patch: {res.patch_path}")
            if res.added_files:
                print(f"Captured {res.added_files} new file(s) in: {res.overlay_dir}")
            if res.skipped_files:
                print(f"Skipped {res.skipped_files} non-text/unreadable file(s).")
            return 0

        if ns.command == "apply":
            res = apply_patches(options=ApplyOptions(patch_dir=Path(ns.patch_dir)))
            if not res.items:
                print("No patches to apply.")
                return 0
            for item in res.items:
                if item.applied:
                    msg = f"Applied: {item.dist_name}=={item.dist_version}"
                    if item.overlay_files_copied:
                        msg += f" (+{item.overlay_files_copied} added file(s))"
                    print(msg)
                else:
                    prefix = f"Skipped: {item.dist_name}=={item.dist_version}" if item.dist_name else "Skipped"
                    print(f"{prefix} ({item.reason})")
            return 0 if res.applied_count else 1

        if ns.command in {"list", "packages"}:
            rows = iter_installed_distributions()
            needle = (ns.contains or "").casefold()
            if needle:
                rows = [(n, v) for n, v in rows if needle in n.casefold()]
            for name, ver in rows:
                if ns.versions:
                    print(f"{name}=={ver}")
                else:
                    print(name)
            return 0

        parser.error("Unknown command")
        return 2
    except PatchKitError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

