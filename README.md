# patch-kit

Create and apply local patches to installed Python distributions.

This is useful when you need to hotfix a third-party dependency locally (for development or CI)
and you want a repeatable way to re-apply the same changes when recreating your environment.

## Install

```bash
pip install patch-kit
```

For contributors:

```bash
pip install -e ".[dev]"
```

## Quickstart

### 1) Patch a dependency locally

1. Install a dependency normally (example: `requests`).
2. Edit the installed files in your environment (site-packages) as needed.
3. If you are unsure of the PyPI distribution name, list what is installed in the **same** environment you use for `patch_kit`:

```bash
patch_kit list
# or: patch_kit packages
# narrow: patch_kit list --contains django
# include versions (name==version): patch_kit list --versions
```

4. Create a patch file:

```bash
patch_kit create requests
```

This writes:
- `patches/requests==<installed_version>.patch` (unified diff for modified files)
- `patches/requests==<installed_version>.files/` (any new files you added)

### 2) Re-apply patches

```bash
patch_kit apply
```

`patch_kit` will:
- Skip patches for distributions that are not installed
- Skip patches where the installed version does not match
- Apply overlay files first, then apply the unified diff

## Notes / limitations

- This tool uses the PyPI package `patch` to apply unified diffs. New files cannot be created via diff hunks, so they are stored and applied separately under `*.files/`.
- Only text files are diffed (decoded as UTF-8). Binary / unreadable files are skipped.

### Using uv

Install and run `patch_kit` with the **same** environment where your dependencies live (the name of the venv folder does not matter):

```bash
uv pip install patch-kit
uv run patch_kit list
uv run patch_kit create <distribution-name>
uv run patch_kit apply
```

If `patch_kit` is already on your `PATH` from an activated uv-managed venv, you can call `patch_kit` directly. For `patch_kit create`, the tool tries `uv pip install … --target` first when `uv` is available; use `patch_kit create --no-uv …` to force `pip` only.

# patch-kit