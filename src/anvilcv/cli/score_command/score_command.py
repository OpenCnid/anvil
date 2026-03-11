"""CLI command for `anvil score` — ATS compatibility checker.

Why:
    `anvil score INPUT` evaluates a resume (PDF or HTML) for ATS compatibility.
    Outputs a color-coded report to terminal or structured JSON/YAML.
"""

from __future__ import annotations

import json
import pathlib
from typing import Annotated

import typer

from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilUserError
from anvilcv.schema.score_report import ScoreReport


@app.command()
def score(
    input_file: Annotated[
        pathlib.Path,
        typer.Argument(
            help="Resume file to score (PDF or HTML).",
            exists=True,
            readable=True,
        ),
    ],
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: text (default) or json.",
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
        pathlib.Path | None,
        typer.Option(
            "--job",
            "-j",
            help="Job description file (text or YAML) for keyword matching.",
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

    Scores a PDF or HTML resume for parsability, structure, and (with --job)
    keyword match against a job description.
    """
    from anvilcv.scoring.ats_scorer import score_document

    job_desc = None
    if job is not None:
        from anvilcv.tailoring.job_parser import parse_job_from_file

        try:
            job_desc = parse_job_from_file(job)
        except AnvilUserError as e:
            typer.echo(f"Error reading job description: {e}", err=True)
            raise typer.Exit(code=1) from None

    try:
        report = score_document(input_file, job=job_desc)
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
    else:
        _print_text_report(report, verbose=verbose, output=output)


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
