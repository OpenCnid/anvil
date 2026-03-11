"""CLI command for `anvil scan` — GitHub repository scanning.

Why:
    `anvil scan --github <user>` fetches repo metadata via GitHub API,
    extracts languages, commit counts, stars, and topics, then generates
    YAML project entries with real metrics. Uses caching and conditional
    requests to minimize API calls.
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import Annotated

import typer

from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilUserError


@app.command(name="scan")
def scan_command(
    github: Annotated[
        str | None,
        typer.Option(
            "--github",
            "-g",
            help="GitHub username to scan.",
        ),
    ] = None,
    output: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output path for scan results.",
        ),
    ] = None,
    merge: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--merge",
            help="Merge generated entries into an existing YAML file.",
            exists=True,
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: yaml (default), json, entries-only.",
        ),
    ] = "yaml",
    max_repos: Annotated[
        int,
        typer.Option(
            "--max-repos",
            help="Maximum repos to scan.",
        ),
    ] = 100,
    since: Annotated[
        str | None,
        typer.Option(
            "--since",
            help="Only repos with activity since DATE (YYYY-MM-DD).",
        ),
    ] = None,
    force_refresh: Annotated[
        bool,
        typer.Option(
            "--force-refresh",
            help="Ignore cache and fetch fresh data.",
        ),
    ] = False,
) -> None:
    """Scan GitHub repositories and generate project entries.

    Fetches public repo metadata, extracts languages and metrics,
    and outputs resume-ready project entries.
    """
    if github is None:
        typer.echo("Error: --github username is required.", err=True)
        raise typer.Exit(code=1)

    from anvilcv.github.cache import (
        read_cached_profile,
        write_cached_profile,
    )
    from anvilcv.github.scanner import scan_user

    # Check for cached data
    profile = None
    if not force_refresh:
        profile = read_cached_profile(github)
        if profile:
            typer.echo(f"Using cached data for {github}.")

    # Fetch fresh data if needed
    if profile is None:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            typer.echo(
                "Warning: No GITHUB_TOKEN set. Rate limited to 60 requests/hour.",
                err=True,
            )

        typer.echo(f"Scanning GitHub repos for {github}...")
        try:
            profile = scan_user(
                username=github,
                token=token,
                max_repos=max_repos,
                since=since,
            )
        except Exception as e:
            typer.echo(f"Error scanning GitHub: {e}", err=True)
            raise typer.Exit(code=3) from None

        # Cache the results
        write_cached_profile(profile)

    if not profile.repos:
        typer.echo(f"No public repositories found for {github}.")
        raise typer.Exit(0)

    typer.echo(f"Found {len(profile.repos)} repos, {profile.summary.total_stars} total stars.")

    # Generate output
    if merge:
        _merge_into_yaml(profile, merge)
        typer.echo(f"Merged {len(profile.repos)} project entries into {merge}.")
    elif format == "json":
        _output_json(profile, output)
    elif format == "entries-only":
        _output_entries_only(profile, output)
    else:
        _output_yaml(profile, output)


def _output_yaml(profile, output_path: pathlib.Path | None) -> None:
    """Write full profile as YAML."""
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.default_flow_style = False
    data = profile.model_dump(mode="json")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            yaml.dump(data, f)
        typer.echo(f"Profile written to {output_path}.")
    else:
        import sys

        yaml.dump(data, sys.stdout)


def _output_json(profile, output_path: pathlib.Path | None) -> None:
    """Write full profile as JSON."""
    data = profile.model_dump(mode="json")
    json_str = json.dumps(data, indent=2, default=str)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str, encoding="utf-8")
        typer.echo(f"Profile written to {output_path}.")
    else:
        typer.echo(json_str)


def _output_entries_only(profile, output_path: pathlib.Path | None) -> None:
    """Write only project entries as YAML."""
    from ruamel.yaml import YAML

    from anvilcv.github.entry_generator import generate_entries

    entries = generate_entries(profile)
    yaml = YAML()
    yaml.default_flow_style = False

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            yaml.dump({"projects": entries}, f)
        typer.echo(f"Entries written to {output_path}.")
    else:
        import sys

        yaml.dump({"projects": entries}, sys.stdout)


def _merge_into_yaml(profile, yaml_path: pathlib.Path) -> None:
    """Merge generated project entries into an existing YAML file."""
    from ruamel.yaml import YAML

    from anvilcv.github.entry_generator import generate_entries

    yaml = YAML()
    yaml.preserve_quotes = True
    with open(yaml_path) as f:
        data = yaml.load(f)

    if not data:
        raise AnvilUserError(message=f"Could not parse {yaml_path}")

    cv = data.get("cv", data)
    sections = cv.setdefault("sections", {})
    entries = generate_entries(profile)
    sections["projects"] = entries

    with open(yaml_path, "w") as f:
        yaml.dump(data, f)
