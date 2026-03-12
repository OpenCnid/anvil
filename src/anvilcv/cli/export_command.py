"""CLI command for `anvil export` — export Anvil YAML to rendercv-compatible format.

Why:
    Users who want to share their YAML with plain rendercv (or contribute
    to the rendercv ecosystem) need to strip the `anvil` section. This
    command does that while preserving all other content, formatting, and
    comments using ruamel.yaml.
"""

from __future__ import annotations

import pathlib
from typing import Annotated

import typer
from ruamel.yaml import YAML

from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilUserError

# Remove the stub from app.py by overriding the command name
# The stub is defined in app.py but we register the real command here


@app.command(name="export")
def export_command(
    input_file: Annotated[
        pathlib.Path,
        typer.Argument(
            help="Anvil YAML input file.",
            exists=True,
            readable=True,
        ),
    ],
    rendercv: Annotated[
        bool,
        typer.Option(
            "--rendercv",
            help="Strip the anvil section for rendercv compatibility.",
        ),
    ] = True,
    output: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path. Defaults to <input>_rendercv.yaml.",
        ),
    ] = None,
) -> None:
    """Export Anvil YAML to rendercv-compatible format.

    Strips the `anvil` and `variant` sections while preserving all other
    content, formatting, and comments.
    """
    yaml = YAML()
    yaml.preserve_quotes = True

    try:
        with open(input_file) as f:
            data = yaml.load(f)
    except Exception as e:
        raise AnvilUserError(message=f"Failed to read {input_file}: {e}") from e

    if data is None:
        raise AnvilUserError(message=f"Empty YAML file: {input_file}")

    # Strip Anvil-specific sections
    removed = []
    for key in ("anvil", "variant"):
        if key in data:
            del data[key]
            removed.append(key)

    if not removed:
        typer.echo("No anvil/variant sections found — file is already rendercv-compatible.")
        raise typer.Exit(0)

    # Determine output path
    if output is None:
        stem = input_file.stem
        output = input_file.parent / f"{stem}_rendercv.yaml"

    try:
        with open(output, "w") as f:
            yaml.dump(data, f)
    except Exception as e:
        raise AnvilUserError(message=f"Failed to write {output}: {e}") from e

    typer.echo(f"Exported to {output} (removed: {', '.join(removed)})")
