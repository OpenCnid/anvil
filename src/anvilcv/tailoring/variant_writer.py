"""Write tailored YAML variants with provenance metadata.

Why:
    Tailored variants are full YAML files with changes tracked via
    provenance metadata. This module NEVER modifies the user's original
    file — the YAML source is sacred (P1 principle).
"""

from __future__ import annotations

import pathlib
from datetime import datetime

from ruamel.yaml import YAML


def write_variant(
    original_data: dict,
    changes: dict[str, str],  # section_path → new content
    source_path: str,
    job_path: str | None,
    provider_name: str,
    model_name: str,
    output_path: pathlib.Path,
) -> pathlib.Path:
    """Write a tailored variant YAML file.

    Applies changes to a copy of the original data and adds provenance
    metadata. Never modifies the original file.
    """
    import copy

    data = copy.deepcopy(original_data)

    # Apply changes
    change_records: list[dict] = []
    for section_path, new_content in changes.items():
        _apply_change(data, section_path, new_content)
        change_records.append(
            {
                "section": section_path,
                "action": "rewritten",
                "detail": "Tailored for job match",
            }
        )

    # Add variant provenance metadata
    data["variant"] = {
        "source": source_path,
        "job": job_path,
        "created_at": datetime.now().isoformat(),
        "provider": provider_name,
        "model": model_name,
        "changes": change_records,
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(output_path, "w") as f:
        yaml.dump(data, f)

    return output_path


def _apply_change(data: dict, section_path: str, new_content: str) -> None:
    """Apply a single change to the data structure.

    section_path format: "experience.0.highlights.2"
    """
    parts = section_path.split(".")
    cv = data.get("cv", data)
    sections = cv.get("sections", cv)

    obj = sections
    for part in parts[:-1]:
        if isinstance(obj, dict):
            obj = obj.get(part, obj)
        elif isinstance(obj, list):
            try:
                obj = obj[int(part)]
            except (ValueError, IndexError):
                return

    last = parts[-1]
    if isinstance(obj, dict):
        obj[last] = new_content
    elif isinstance(obj, list):
        try:
            obj[int(last)] = new_content
        except (ValueError, IndexError):
            pass
