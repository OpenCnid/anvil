"""CLI command for `anvil prep` — generate interview preparation notes.

Why:
    `anvil prep INPUT --job <path>` reads a resume YAML and job description,
    uses AI to generate per-project talking points matched to job requirements,
    and writes Markdown output.
"""

from __future__ import annotations

import asyncio
import pathlib
from typing import Annotated

import typer
from ruamel.yaml import YAML

from anvilcv.ai.provider import AIProvider
from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilAIProviderError, AnvilUserError


@app.command(name="prep")
def prep_command(
    input_file: Annotated[
        pathlib.Path,
        typer.Argument(
            help="Anvil/rendercv YAML input file.",
            exists=True,
            readable=True,
        ),
    ],
    job: Annotated[
        pathlib.Path,
        typer.Option(
            "--job",
            "-j",
            help="Job description file (text or YAML).",
            exists=True,
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
            help="Output path for prep notes.",
        ),
    ] = None,
) -> None:
    """Generate interview preparation notes for a job.

    Reads your resume and a job description, matches skills and experience,
    then generates structured talking points for each project/experience entry.
    """
    from anvilcv.tailoring.job_parser import parse_job_from_file
    from anvilcv.tailoring.matcher import match_resume_to_job

    # Parse job description
    try:
        job_desc = parse_job_from_file(job)
    except AnvilUserError as e:
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
    provider_instance = _resolve_provider(
        provider_name=provider,
        resume_data=resume_data,
    )

    # Generate prep notes
    from anvilcv.prep.generator import generate_prep_notes, write_prep_notes

    try:
        content = asyncio.run(generate_prep_notes(provider_instance, resume_data, job_desc, match))
    except AnvilAIProviderError as e:
        typer.echo(f"AI error: {e}", err=True)
        raise typer.Exit(code=4) from None

    # Write output
    if output is None:
        cv_name = resume_data.get("cv", {}).get("name", "Resume")
        safe_name = cv_name.replace(" ", "_")
        output = pathlib.Path(f"{safe_name}_prep.md")

    write_prep_notes(content, output)
    typer.echo(f"Prep notes written to {output}")


def _resolve_provider(
    provider_name: str | None,
    resume_data: dict,
) -> AIProvider:
    """Resolve which AI provider to use."""
    from anvilcv.ai.anthropic import AnthropicProvider
    from anvilcv.ai.ollama import OllamaProvider
    from anvilcv.ai.openai import OpenAIProvider

    anvil_config = resume_data.get("anvil", {})
    providers_config = anvil_config.get("providers", {})

    if provider_name is None:
        provider_name = providers_config.get("default", "anthropic")

    provider_map = {
        "anthropic": lambda: AnthropicProvider(
            model=providers_config.get("anthropic", {}).get("model"),
        ),
        "openai": lambda: OpenAIProvider(
            model=providers_config.get("openai", {}).get("model"),
        ),
        "ollama": lambda: OllamaProvider(
            model=providers_config.get("ollama", {}).get("model"),
            base_url=providers_config.get("ollama", {}).get("base_url"),
        ),
    }

    factory = provider_map.get(provider_name)
    if factory is None:
        raise AnvilUserError(
            message=(f"Unknown provider: {provider_name}. Supported: anthropic, openai, ollama")
        )

    provider_instance = factory()
    if not provider_instance.is_configured():
        instructions = provider_instance.get_setup_instructions()
        raise AnvilAIProviderError(
            message=(f"Provider {provider_name} is not configured.\n{instructions}")
        )

    return provider_instance
