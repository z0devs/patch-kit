from __future__ import annotations


class PatchKitError(Exception):
    """Base exception for patch-kit."""


class DistributionNotFoundError(PatchKitError):
    def __init__(self, dist_name: str, suggestions: list[str] | None = None):
        self.dist_name = dist_name
        self.suggestions = suggestions or []
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if not self.suggestions:
            return (
                f"Distribution not found: {self.dist_name!r}. "
                "Run `patch_kit list` to see installed names."
            )
        joined = " or ".join(repr(s) for s in self.suggestions)
        return f"Distribution not found: {self.dist_name!r}. Did you mean {joined}?"


class SitePackagesNotFoundError(PatchKitError):
    pass


class DownloadError(PatchKitError):
    def __init__(
        self,
        dist_spec: str,
        attempted_commands: list[list[str]],
        stdout: str | None = None,
        stderr: str | None = None,
        returncode: int | None = None,
        underlying: Exception | None = None,
    ):
        self.dist_spec = dist_spec
        self.attempted_commands = attempted_commands
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.underlying = underlying
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        cmds = " | ".join(" ".join(c) for c in self.attempted_commands)
        base = f"Failed to download {self.dist_spec} using: {cmds}"
        if self.returncode is not None:
            base += f" (exit code {self.returncode})"
        if self.underlying is not None:
            base += f": {self.underlying}"
        return base


class PatchWriteError(PatchKitError):
    pass


class PatchLoadError(PatchKitError):
    pass


class PatchApplyError(PatchKitError):
    def __init__(self, patch_path: str, message: str | None = None):
        self.patch_path = patch_path
        self.message = message or "Patch failed to apply"
        super().__init__(f"{self.message}: {self.patch_path}")


class OverlayApplyError(PatchKitError):
    pass

