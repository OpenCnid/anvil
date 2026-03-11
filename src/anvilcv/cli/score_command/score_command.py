"""CLI command for `anvil score` — ATS compatibility checker.

Why:
    `anvil score INPUT` evaluates a resume (PDF, HTML, or YAML) for ATS compatibility.
    Outputs a color-coded report to terminal or structured JSON/YAML.
    If YAML is provided, Anvil renders it first, then scores the output.
"""

from __future__ import annotations

import json
import pathlib
from typing import Annotated

import typer

from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilServiceError, AnvilUserError
from anvilcv.schema.score_report import ScoreReport


@app.command()
def score(
    input_file: Annotated[
        pathlib.Path,
        typer.Argument(
            help="Resume file to score (PDF, HTML, or YAML).",
            exists=True,
            readable=True,
        ),
    ],
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: text (default), json, or yaml.",
        ),
    ] = "text",
    output: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write report to file instead of stdout.",
        ),
    ] = None,
    job: Annotated[
        str | None,
        typer.Option(
            "--job",
            "-j",
            help="Job description: file path, URL, or '-' for stdin.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed check information.",
        ),
    ] = False,
) -> None:
    """Check ATS compatibility of a resume file.

    Scores a PDF, HTML, or YAML resume for parsability, structure, and (with --job)
    keyword match against a job description. YAML inputs are rendered first.
    """
    from anvilcv.scoring.text_extractor import extract_text

    # If input is YAML, render it first and score the HTML output
    scorable_file = input_file
    if input_file.suffix in (".yaml", ".yml"):
        scorable_file = _render_yaml_for_scoring(input_file)

    # Extract text and check for PDF extraction issues
    try:
        doc = extract_text(scorable_file)
    except AnvilUserError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from None

    if doc.is_empty and doc.source_type == "pdf":
        typer.echo(
            f"Could not extract text from {scorable_file}. "
            "The PDF may be image-based (scanned) rather than "
            "machine-readable. Try scoring the HTML output instead: "
            "`anvil score output/resume.html`",
            err=True,
        )
        raise typer.Exit(code=1) from None

    if doc.is_partial and doc.source_type == "pdf":
        extracted = doc.page_count - doc.image_page_count
        typer.echo(
            f"Warning: Text extraction from {scorable_file} may be "
            f"incomplete. {extracted} pages extracted, "
            f"{doc.image_page_count} appear to be images. "
            "Score may be inaccurate.",
            err=True,
        )

    # Parse job description if provided
    job_desc = None
    if job is not None:
        from anvilcv.cli.job_input import resolve_job_input

        try:
            job_desc = resolve_job_input(job)
        except AnvilServiceError as e:
            # Per spec: URL errors → warn and continue with structure-only scoring
            typer.echo(f"Warning: {e}", err=True)
            typer.echo("Scoring without job keywords.", err=True)
        except AnvilUserError as e:
            typer.echo(f"Error reading job description: {e}", err=True)
            raise typer.Exit(code=1) from None

    try:
        from anvilcv.scoring.ats_scorer import score_extracted_document

        report = score_extracted_document(doc, file_path=str(scorable_file), job=job_desc)
    except AnvilUserError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from None

    if format == "json":
        report_dict = report.model_dump(mode="json")
        json_output = json.dumps(report_dict, indent=2, default=str)
        if output:
            output.write_text(json_output)
            typer.echo(f"Report written to {output}")
        else:
            typer.echo(json_output)
    elif format == "yaml":
        _print_yaml_report(report, output=output)
    else:
        _print_text_report(report, verbose=verbose, output=output)


def _render_yaml_for_scoring(yaml_path: pathlib.Path) -> pathlib.Path:
    """Render a YAML resume and return the path to the ATS HTML output for scoring.

    Why ATS HTML: semantic structure is the most reliable format for text
    extraction and scoring, better than PDF or styled HTML.
    """
    import tempfile

    from anvilcv.vendor.rendercv.renderer.html import generate_ats_html, generate_html
    from anvilcv.vendor.rendercv.renderer.markdown import generate_markdown
    from anvilcv.vendor.rendercv.schema.rendercv_model_builder import (
        build_rendercv_dictionary_and_model,
    )

    try:
        main_yaml = yaml_path.read_text(encoding="utf-8")
        output_dir = pathlib.Path(tempfile.mkdtemp(prefix="anvil_score_"))

        _, model = build_rendercv_dictionary_and_model(
            main_yaml,
            input_file_path=yaml_path,
            output_folder=str(output_dir),
        )

        # Try ATS HTML first (best for scoring)
        ats_path = generate_ats_html(model)
        if ats_path and ats_path.exists():
            return ats_path

        # Fall back to regular HTML via Markdown
        md_path = generate_markdown(model)
        html_path = generate_html(model, md_path)
        if html_path and html_path.exists():
            return html_path

        raise AnvilUserError(message=f"Rendering {yaml_path} produced no scorable output.")
    except AnvilUserError:
        raise
    except Exception as e:
        raise AnvilUserError(message=f"Failed to render {yaml_path} for scoring: {e}") from e


def _print_yaml_report(
    report: ScoreReport,
    output: pathlib.Path | None = None,
) -> None:
    """Print a YAML-formatted report."""
    import yaml  # type: ignore[import-untyped]

    report_dict = report.model_dump(mode="json")
    yaml_output = yaml.dump(report_dict, default_flow_style=False, sort_keys=False)
    if output:
        output.write_text(yaml_output)
        typer.echo(f"Report written to {output}")
    else:
        typer.echo(yaml_output)


def _print_text_report(
    report: ScoreReport,
    verbose: bool = False,
    output: pathlib.Path | None = None,
) -> None:
    """Print a formatted text report."""

    lines: list[str] = []

    # Header
    score = report.overall_score
    lines.append("")
    lines.append("=" * 40)
    lines.append("     ATS Compatibility Report")
    lines.append(f"        Score: {score}/100")
    lines.append("=" * 40)
    lines.append("")

    # Parsability
    lines.append(f"Parsability: {report.parsability.score}/100")
    for check in report.parsability.checks:
        icon = _status_icon(check.status)
        conf = f"  [{check.confidence.replace('_', ' ')}]" if verbose else ""
        lines.append(f"  {icon} {check.name}{conf}")
        if check.detail and (verbose or check.status != "pass"):
            lines.append(f"    {check.detail}")

    lines.append("")

    # Structure
    lines.append(f"Structure: {report.structure.score}/100")
    for check in report.structure.checks:
        icon = _status_icon(check.status)
        conf = f"  [{check.confidence.replace('_', ' ')}]" if verbose else ""
        lines.append(f"  {icon} {check.name}{conf}")
        if check.detail and (verbose or check.status != "pass"):
            lines.append(f"    {check.detail}")

    lines.append("")

    # Keywords (if present)
    if report.keyword_match:
        km = report.keyword_match
        lines.append(f"Keywords: {km.score}/100")
        if km.matched:
            lines.append(f"  Matched: {', '.join(km.matched)}")
        if km.missing:
            lines.append(f"  Missing: {', '.join(km.missing)}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("Recommendations:")
        for rec in report.recommendations:
            priority = rec.priority.upper()
            lines.append(f"  [{priority}] {rec.message}")
        lines.append("")

    text = "\n".join(lines)
    if output:
        output.write_text(text)
        typer.echo(f"Report written to {output}")
    else:
        typer.echo(text)


def _status_icon(status: str) -> str:
    """Return a text icon for check status."""
    return {"pass": "[PASS]", "fail": "[FAIL]", "warn": "[WARN]"}.get(status, "[????]")
