from __future__ import annotations

from collections import defaultdict
from difflib import get_close_matches
from itertools import chain
from importlib.metadata import distributions


def iter_installed_distributions() -> list[tuple[str, str]]:
    """
    Installed (name, version) pairs for the current interpreter, sorted by name.

    Uses ``distributions()`` so every install is listed (unlike ``top_level.txt`` mapping).
    If the same name appears more than once, the first seen row is kept.
    """
    by_key: dict[str, tuple[str, str]] = {}
    for dist in distributions():
        raw_name = (dist.metadata.get("Name") or dist.name or "").strip()
        if not raw_name:
            continue
        ver = (dist.version or "").strip()
        key = raw_name.casefold()
        if key not in by_key:
            by_key[key] = (raw_name, ver)
    return sorted(by_key.values(), key=lambda nv: nv[0].casefold())


def packages_distributions() -> dict[str, list[str]]:
    """
    Map top-level import packages to distribution names.

    This is best-effort because:
    - Not all dists ship `top_level.txt`
    - Some dists provide multiple top-level packages
    """
    pkg_to_dist: dict[str, list[str]] = defaultdict(list)
    for dist in distributions():
        try:
            # Python 3.13+: read_text no longer accepts encoding= (always UTF-8).
            try:
                top_level = dist.read_text("top_level.txt", encoding="utf-8") or ""
            except TypeError:
                top_level = dist.read_text("top_level.txt") or ""
        except (UnicodeDecodeError, FileNotFoundError):
            top_level = ""
        for pkg in top_level.split():
            name = dist.metadata.get("Name")
            if name:
                pkg_to_dist[pkg].append(name)
    return dict(pkg_to_dist)


def suggest_distributions(name: str) -> list[str]:
    """
    Return a list of best-effort distribution name suggestions for a user input.
    """
    dists = packages_distributions()
    if name in dists:
        return dists[name]
    matches = get_close_matches(name, chain(*dists.values()))
    if matches:
        return matches
    pkg_matches = get_close_matches(name, dists.keys(), 1)
    if pkg_matches:
        return dists[pkg_matches[0]]
    return []

