from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import patch  # type: ignore


@dataclass(frozen=True)
class PatchApplyOutcome:
    applied: bool
    last_message: str | None = None


class _LastMessageHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.last_message: str | None = None

    def emit(self, record: logging.LogRecord) -> None:
        self.last_message = record.getMessage()


def apply_patch_file(*, patch_path: Path, root: Path) -> PatchApplyOutcome:
    """
    Apply a unified diff patch file using the `patch` dependency.

    The underlying library reports some details via logging; we capture the last
    message for diagnostics, but we do not treat it as a stable API.
    """
    logger = logging.getLogger("patch")
    handler = _LastMessageHandler()
    logger.addHandler(handler)
    try:
        patchset = patch.fromfile(str(patch_path))
        if not patchset:
            return PatchApplyOutcome(applied=False, last_message=handler.last_message)
        applied = bool(patchset.apply(root=str(root)))
        return PatchApplyOutcome(applied=applied, last_message=handler.last_message)
    finally:
        logger.removeHandler(handler)

