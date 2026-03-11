"""CLI command for `anvil cover` — generate a cover letter.

Why:
    `anvil cover INPUT --job <path-or-url>` reads a resume YAML and job description,
    uses AI to generate a targeted cover letter that references actual projects
    and metrics from the resume. Output is Markdown.
"""

from __future__ import annotations

import asyncio
import pathlib
from typing import Annotated

import typer
from ruamel.yaml import YAML

from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilAIProviderError, AnvilUserError


@app.command(name="cover")
def cover_command(
    input_file: Annotated[
        pathlib.Path,
        typer.Argument(
            help="Anvil/rendercv YAML input file.",
            exists=True,
            readable=True,
        ),
    ],
    job: Annotated[
        str,
        typer.Option(
            "--job",
            "-j",
            help="Job description: file path, URL, or '-' for stdin.",
        ),
    ],
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            "-p",
            help="AI provider (anthropic, openai, ollama).",
        ),
    ] = None,
    output: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output path for cover letter.",
        ),
    ] = None,
    render: Annotated[
        bool,
        typer.Option(
            "--render",
            help="Also render cover letter to PDF (requires Typst template).",
        ),
    ] = False,
) -> None:
    """Generate a cover letter from your resume and a job description.

    Reads your resume and a job description, matches skills, then generates
    a targeted cover letter that references actual projects and achievements.
    """
    from anvilcv.cli.job_input import resolve_job_input
    from anvilcv.tailoring.matcher import match_resume_to_job

    # Parse job description (URL, file, or stdin)
    try:
        job_desc = resolve_job_input(job)
    except (AnvilUserError, Exception) as e:
        typer.echo(f"Error reading job description: {e}", err=True)
        raise typer.Exit(code=1) from None

    # Read resume YAML
    yaml = YAML()
    try:
        with open(input_file) as f:
            resume_data = yaml.load(f)
    except Exception as e:
        typer.echo(f"Error reading resume: {e}", err=True)
        raise typer.Exit(code=1) from None

    # Match resume to job
    match = match_resume_to_job(resume_data, job_desc)

    typer.echo(
        f"Matched {len(match.matches)} entries, "
        f"{len(match.missing_required)} missing required skills."
    )

    # Resolve provider
    from anvilcv.cli.provider_resolver import resolve_provider

    provider_instance = resolve_provider(
        provider_name=provider,
        resume_data=resume_data,
    )

    # Generate cover letter
    from anvilcv.cover.generator import generate_cover_letter, write_cover_letter

    try:
        content = asyncio.run(
            generate_cover_letter(provider_instance, resume_data, job_desc, match)
        )
    except AnvilAIProviderError as e:
        typer.echo(f"AI error: {e}", err=True)
        raise typer.Exit(code=4) from None

    # Write output
    if output is None:
        cv_name = resume_data.get("cv", {}).get("name", "Resume")
        safe_name = cv_name.replace(" ", "_")
        output = pathlib.Path(f"{safe_name}_cover.md")

    write_cover_letter(content, output)
    typer.echo(f"Cover letter written to {output}")

    if render:
        typer.echo(
            "Note: --render for cover letters requires a Typst template (P2 stretch goal). "
            "Not yet implemented."
        )
