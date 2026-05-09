from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def __getattr__(name: str):
    if name == "__version__":
        try:
            return version("patch-kit")
        except PackageNotFoundError:
            return "0.0.0"
    raise AttributeError(name)


__all__ = ["__version__"]

