from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .errors import DownloadError


def download_dist_to_target(
    *,
    dist_name: str,
    dist_version: str,
    target_dir: Path,
    prefer_uv: bool = True,
) -> None:
    """
    Download and install the exact dist version into target_dir (no deps).

    Strategy:
    - Try `uv pip install ... --target ...` first if prefer_uv.
    - Fallback to `python -m pip install ... --target ...`.
    """
    dist_spec = f"{dist_name}=={dist_version}"
    target_dir.mkdir(parents=True, exist_ok=True)

    commands: list[list[str]] = []
    if prefer_uv:
        commands.append(
            [
                "uv",
                "pip",
                "install",
                dist_spec,
                "--target",
                str(target_dir),
                "--no-deps",
                "--upgrade",
            ]
        )
    commands.append(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            dist_spec,
            "--target",
            str(target_dir),
            "--no-deps",
            "--upgrade",
        ]
    )

    last_exc: Exception | None = None
    for cmd in commands:
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return
        except FileNotFoundError as e:
            last_exc = e
            continue
        except subprocess.CalledProcessError as e:
            last_exc = e
            continue

    stdout = getattr(last_exc, "stdout", None)
    stderr = getattr(last_exc, "stderr", None)
    returncode = getattr(last_exc, "returncode", None)
    raise DownloadError(
        dist_spec=dist_spec,
        attempted_commands=commands,
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
        underlying=last_exc,
    )

