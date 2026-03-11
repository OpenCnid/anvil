"""CLI command for `anvil tailor` — AI-tailor resume to a job description.

Why:
    `anvil tailor INPUT --job <path-or-url>` reads a resume YAML and job description,
    uses AI to rewrite relevant bullet points, and writes a tailored variant
    to the variants/ directory. Never modifies the original file.
    Supports --render and --score for end-to-end pipeline composition.
"""

from __future__ import annotations

import asyncio
import pathlib
from typing import TYPE_CHECKING, Annotated

import typer
from ruamel.yaml import YAML

from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilAIProviderError, AnvilUserError

if TYPE_CHECKING:
    from anvilcv.schema.job_description import JobDescription


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
    render: Annotated[
        bool,
        typer.Option(
            "--render",
            help="Also render the tailored variant after generating.",
        ),
    ] = False,
    score: Annotated[
        bool,
        typer.Option(
            "--score",
            help="Also score the tailored variant (implies --render).",
        ),
    ] = False,
) -> None:
    """AI-tailor your resume to a specific job description.

    Reads your resume YAML and a job description, identifies the most
    relevant bullets, rewrites them using AI to match the job, and
    writes a tailored variant with provenance metadata.
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
    from anvilcv.cli.provider_resolver import resolve_provider

    provider_instance = resolve_provider(
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
        job_path=job,
        provider_name=provider_instance.name,
        model_name=model or "default",
        output_path=output,
    )

    typer.echo(f"Variant written to {variant_path} ({len(changes)} changes)")

    # --score implies --render
    if score:
        render = True

    # Post-processing: render the variant
    if render:
        _render_variant(variant_path)

    # Post-processing: score the variant
    if score:
        _score_variant(variant_path, job_desc)


def _render_variant(variant_path: pathlib.Path) -> None:
    """Render a tailored variant using the render pipeline."""
    typer.echo(f"Rendering {variant_path}...")
    try:
        from anvilcv.vendor.rendercv.renderer.html import generate_ats_html, generate_html
        from anvilcv.vendor.rendercv.renderer.markdown import generate_markdown
        from anvilcv.vendor.rendercv.renderer.typst import generate_typst
        from anvilcv.vendor.rendercv.schema.rendercv_model_builder import (
            build_rendercv_dictionary_and_model,
        )

        main_yaml = variant_path.read_text(encoding="utf-8")
        _, model = build_rendercv_dictionary_and_model(
            main_yaml,
            input_file_path=variant_path,
        )

        generate_typst(model)
        md_path = generate_markdown(model)
        generate_html(model, md_path)
        generate_ats_html(model)

        typer.echo(f"Rendered variant outputs alongside {variant_path}")
    except Exception as e:
        typer.echo(f"Warning: rendering failed: {e}", err=True)


def _score_variant(
    variant_path: pathlib.Path,
    job_desc: "JobDescription | None" = None,
) -> None:
    """Score a rendered variant against the job description."""
    typer.echo("Scoring variant...")
    try:
        from anvilcv.cli.score_command.score_command import _render_yaml_for_scoring
        from anvilcv.scoring.ats_scorer import score_document

        scorable = _render_yaml_for_scoring(variant_path)
        report = score_document(scorable, job=job_desc)

        typer.echo(f"\nVariant ATS Score: {report.overall_score}/100")
        if report.keyword_match:
            typer.echo(f"  Keyword match: {report.keyword_match.score}/100")
            if report.keyword_match.missing:
                typer.echo(f"  Missing keywords: {', '.join(report.keyword_match.missing[:10])}")
    except Exception as e:
        typer.echo(f"Warning: scoring failed: {e}", err=True)
