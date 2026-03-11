"""Fork integrity CI check.

Ensures that all vendored files which are supposed to remain untouched are
byte-for-byte identical to the upstream baseline (rendercv v2.7).

Files that have been intentionally *Modified* or *Extended* in the fork are
skipped — see specs/architecture.md module inventory for classifications.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASELINE_DIR = _REPO_ROOT / "baseline" / "rendercv-v2.7"
_VENDOR_DIR = _REPO_ROOT / "src" / "anvilcv" / "vendor" / "rendercv"

# ---------------------------------------------------------------------------
# Intentionally changed files — Modified or Extended per specs/architecture.md.
# These are NOT checked against the baseline.
# Paths are relative to the rendercv root (both baseline and vendor).
# ---------------------------------------------------------------------------

MODIFIED_FILES: frozenset[str] = frozenset(
    {
        # Modified (4) — internals changed
        "__init__.py",
        "__main__.py",
        "cli/entry_point.py",
        "cli/app.py",
        # Extended — functionality added
        "cli/error_handler.py",
        "cli/render_command/render_command.py",
        "cli/render_command/run_rendercv.py",
        "renderer/html.py",
        "renderer/templater/templater.py",
        "schema/models/design/built_in_design.py",
    }
)

# ---------------------------------------------------------------------------
# Collect every file in the baseline that is NOT in the Modified set.
# ---------------------------------------------------------------------------


def _collect_untouched_files() -> list[str]:
    """Return sorted list of relative paths (as POSIX strings) for all files
    in the baseline directory that should remain untouched in the vendor tree."""
    if not _BASELINE_DIR.is_dir():
        return []

    untouched: list[str] = []
    for path in sorted(_BASELINE_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(_BASELINE_DIR).as_posix()
        if rel not in MODIFIED_FILES:
            untouched.append(rel)
    return untouched


_UNTOUCHED_FILES = _collect_untouched_files()

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel_path", _UNTOUCHED_FILES, ids=_UNTOUCHED_FILES)
def test_untouched_file_matches_baseline(rel_path: str) -> None:
    """Each untouched vendored file must be byte-for-byte identical to its
    baseline counterpart."""
    baseline_file = _BASELINE_DIR / rel_path
    vendor_file = _VENDOR_DIR / rel_path

    assert vendor_file.exists(), (
        f"Untouched file missing from vendor tree: {rel_path}\n"
        f"  expected at: {vendor_file}"
    )

    baseline_bytes = baseline_file.read_bytes()
    vendor_bytes = vendor_file.read_bytes()

    assert baseline_bytes == vendor_bytes, (
        f"Untouched vendored file differs from baseline: {rel_path}\n"
        f"  baseline: {baseline_file}\n"
        f"  vendor:   {vendor_file}\n"
        f"This file should NOT be modified in the fork. "
        f"Restore it from the baseline or remove it from the untouched set "
        f"if the change is intentional."
    )
