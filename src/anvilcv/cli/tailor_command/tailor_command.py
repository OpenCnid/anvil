"""CLI command for `anvil tailor` — AI-tailor resume to a job description.

Why:
    `anvil tailor INPUT --job <path>` reads a resume YAML and job description,
    uses AI to rewrite relevant bullet points, and writes a tailored variant
    to the variants/ directory. Never modifies the original file.
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


@app.command(name="tailor")
def tailor_command(
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
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="AI model to use.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be changed without writing.",
        ),
    ] = False,
    output: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output path for the variant file.",
        ),
    ] = None,
    max_rewrites: Annotated[
        int,
        typer.Option(
            "--max-rewrites",
            help="Maximum number of bullets to rewrite.",
        ),
    ] = 10,
) -> None:
    """AI-tailor your resume to a specific job description.

    Reads your resume YAML and a job description, identifies the most
    relevant bullets, rewrites them using AI to match the job, and
    writes a tailored variant with provenance metadata.
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

    if not match.matches:
        typer.echo("No matchable bullet points found in resume.")
        raise typer.Exit(0)

    typer.echo(
        f"Found {len(match.matches)} bullets, "
        f"{len(match.missing_required)} missing required skills."
    )

    if dry_run:
        typer.echo("\nDry run — top matches:")
        for m in match.matches[:max_rewrites]:
            skills = ", ".join(m.matched_skills) if m.matched_skills else "none"
            typer.echo(f"  [{m.section_path}] ({skills}): {m.content[:80]}")
        if match.missing_required:
            typer.echo(f"\nMissing required: {', '.join(match.missing_required)}")
        raise typer.Exit(0)

    # Resolve provider
    provider_instance = _resolve_provider(
        provider_name=provider,
        model_name=model,
        resume_data=resume_data,
    )

    # Get bullets to rewrite (top by relevance)
    bullets_to_rewrite = [
        (m.section_path, m.content) for m in match.matches if m.relevance_score > 0
    ][:max_rewrites]

    if not bullets_to_rewrite:
        typer.echo("No relevant bullets to rewrite.")
        raise typer.Exit(0)

    typer.echo(f"Rewriting {len(bullets_to_rewrite)} bullets...")

    # Run AI rewriting
    from anvilcv.tailoring.rewriter import rewrite_top_bullets

    try:
        changes = asyncio.run(
            rewrite_top_bullets(
                provider_instance,
                bullets_to_rewrite,
                job_desc,
                match,
                max_rewrites=max_rewrites,
            )
        )
    except AnvilAIProviderError as e:
        typer.echo(f"AI error: {e}", err=True)
        raise typer.Exit(code=4) from None

    if not changes:
        typer.echo("No changes made — bullets already well-matched.")
        raise typer.Exit(0)

    # Write variant
    from anvilcv.tailoring.variant_writer import write_variant

    if output is None:
        cv_name = resume_data.get("cv", {}).get("name", "Resume")
        safe_name = cv_name.replace(" ", "_")
        company = job_desc.company.replace(" ", "_")
        date = __import__("datetime").date.today().isoformat()
        output = pathlib.Path(f"variants/{safe_name}_{company}_{date}.yaml")

    variant_path = write_variant(
        original_data=resume_data,
        changes=changes,
        source_path=str(input_file),
        job_path=str(job),
        provider_name=provider_instance.name,
        model_name=model or "default",
        output_path=output,
    )

    typer.echo(f"Variant written to {variant_path} ({len(changes)} changes)")


def _resolve_provider(
    provider_name: str | None,
    model_name: str | None,
    resume_data: dict,
) -> AIProvider:
    """Resolve which AI provider to use."""
    from anvilcv.ai.anthropic import AnthropicProvider
    from anvilcv.ai.ollama import OllamaProvider
    from anvilcv.ai.openai import OpenAIProvider

    # Check YAML config first
    anvil_config = resume_data.get("anvil", {})
    providers_config = anvil_config.get("providers", {})

    if provider_name is None:
        provider_name = providers_config.get("default", "anthropic")

    provider_map = {
        "anthropic": lambda: AnthropicProvider(
            model=model_name or providers_config.get("anthropic", {}).get("model"),
        ),
        "openai": lambda: OpenAIProvider(
            model=model_name or providers_config.get("openai", {}).get("model"),
        ),
        "ollama": lambda: OllamaProvider(
            model=model_name or providers_config.get("ollama", {}).get("model"),
            base_url=providers_config.get("ollama", {}).get("base_url"),
        ),
    }

    factory = provider_map.get(provider_name)
    if factory is None:
        raise AnvilUserError(
            message=(f"Unknown provider: {provider_name}. Supported: anthropic, openai, ollama")
        )

    provider = factory()
    if not provider.is_configured():
        instructions = provider.get_setup_instructions()
        raise AnvilAIProviderError(
            message=(f"Provider {provider_name} is not configured.\n{instructions}")
        )

    return provider
