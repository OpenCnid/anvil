"""Batch rendering for variant YAML files.

Why:
    `anvil render --variant <dir>` renders all YAML files in a variants
    directory. Each variant gets its own output subfolder named after the
    variant file, preserving provenance metadata in the output structure.
"""

from __future__ import annotations

import pathlib
from typing import Any

from ruamel.yaml import YAML


def discover_variants(variant_dir: pathlib.Path) -> list[pathlib.Path]:
    """Find all YAML variant files in a directory.

    Returns files sorted alphabetically for deterministic ordering.
    """
    if not variant_dir.is_dir():
        return []

    variants: list[pathlib.Path] = []
    for ext in ("*.yaml", "*.yml"):
        variants.extend(variant_dir.glob(ext))

    return sorted(variants)


def get_variant_output_folder(
    variant_path: pathlib.Path,
    base_output: pathlib.Path | None = None,
) -> pathlib.Path:
    """Compute the output folder for a variant file.

    Each variant gets a subfolder named after the variant file stem
    (e.g., `variants/Jane_Acme_2026-03-11.yaml` → `rendercv_output/Jane_Acme_2026-03-11/`).

    Args:
        variant_path: Path to the variant YAML file.
        base_output: Base output directory. Defaults to `rendercv_output` next to variant.

    Returns:
        Output folder path for this variant.
    """
    if base_output is None:
        base_output = variant_path.parent / "rendercv_output"

    return base_output / variant_path.stem


def read_variant_metadata(variant_path: pathlib.Path) -> dict[str, Any] | None:
    """Read variant provenance metadata from a YAML file.

    Returns the `variant` section if present, None otherwise.
    """
    yaml = YAML()
    try:
        with open(variant_path) as f:
            data = yaml.load(f)
        if data and isinstance(data, dict):
            result: dict[str, Any] | None = data.get("variant")
            return result
    except Exception:
        return None
    return None


def render_variant(
    variant_path: pathlib.Path,
    output_folder: pathlib.Path | None = None,
    **render_kwargs,
) -> pathlib.Path:
    """Render a single variant YAML file.

    Delegates to the vendored rendercv render pipeline with a variant-specific
    output folder.

    Args:
        variant_path: Path to the variant YAML file.
        output_folder: Override output folder. Auto-computed if None.
        **render_kwargs: Additional arguments passed to the render pipeline.

    Returns:
        Path to the output folder containing rendered files.
    """
    from anvilcv.vendor.rendercv.cli.render_command.progress_panel import (
        ProgressPanel,
    )
    from anvilcv.vendor.rendercv.cli.render_command.run_rendercv import run_rendercv

    out = output_folder or get_variant_output_folder(variant_path)

    with ProgressPanel(quiet=True) as progress:
        run_rendercv(
            variant_path,
            progress,
            output_folder=out,
            **render_kwargs,
        )

    return out


def render_all_variants(
    variant_dir: pathlib.Path,
    base_output: pathlib.Path | None = None,
    **render_kwargs,
) -> list[tuple[pathlib.Path, pathlib.Path]]:
    """Render all variant YAML files in a directory.

    Args:
        variant_dir: Directory containing variant YAML files.
        base_output: Base output directory for all variants.
        **render_kwargs: Additional arguments passed to each render.

    Returns:
        List of (variant_path, output_folder) pairs for successfully rendered variants.
    """
    variants = discover_variants(variant_dir)
    results: list[tuple[pathlib.Path, pathlib.Path]] = []

    for variant_path in variants:
        out = get_variant_output_folder(variant_path, base_output)
        try:
            render_variant(variant_path, output_folder=out, **render_kwargs)
            results.append((variant_path, out))
        except Exception:
            # Individual variant failures shouldn't stop the batch
            pass

    return results
