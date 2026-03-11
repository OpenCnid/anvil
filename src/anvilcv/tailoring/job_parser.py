"""Job description parser — multi-source input handling.

Why:
    Job descriptions come from URLs, local files, or stdin.
    This module handles all three sources with best-effort extraction.
"""

from __future__ import annotations

import pathlib
import sys

from anvilcv.exceptions import AnvilUserError
from anvilcv.schema.job_description import JobDescription, JobRequirements
from anvilcv.scoring.keyword_extractor import (
    categorize_skills,
    extract_experience_years,
)


def parse_job_from_file(path: pathlib.Path) -> JobDescription:
    """Parse a job description from a local file (plain text or YAML)."""
    if not path.exists():
        raise AnvilUserError(message=f"Job description file not found: {path}")

    text = path.read_text(encoding="utf-8")

    # Try YAML first (structured job description)
    if path.suffix in (".yaml", ".yml"):
        return _parse_yaml_job(text, source="file")

    # Plain text
    return _parse_text_job(text, source="file")


def parse_job_from_text(text: str, source: str = "stdin") -> JobDescription:
    """Parse a job description from raw text."""
    return _parse_text_job(text, source=source)


def parse_job_from_stdin() -> JobDescription:
    """Parse a job description from stdin."""
    if sys.stdin.isatty():
        raise AnvilUserError(
            message="No job description on stdin. Pipe text or use --job <file>."
        )
    text = sys.stdin.read()
    return _parse_text_job(text, source="stdin")


def _parse_text_job(text: str, source: str = "file") -> JobDescription:
    """Extract structured data from raw job description text."""
    required_skills, preferred_skills = categorize_skills(text)
    experience_years = extract_experience_years(text)

    # Try to extract title and company from first few lines
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    title = lines[0] if lines else "Unknown Position"
    company = lines[1] if len(lines) > 1 else "Unknown Company"

    # Truncate if they look like full paragraphs
    if len(title) > 100:
        title = "Unknown Position"
    if len(company) > 100:
        company = "Unknown Company"

    return JobDescription(
        title=title,
        company=company,
        source=source if source in ("url", "file", "stdin") else "file",
        requirements=JobRequirements(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=experience_years,
        ),
        raw_text=text,
    )


def _parse_yaml_job(text: str, source: str = "file") -> JobDescription:
    """Parse a structured YAML job description."""
    import yaml

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise AnvilUserError(
            message=f"Invalid YAML in job description: {e}"
        ) from e

    if not isinstance(data, dict):
        raise AnvilUserError(
            message="Job description YAML must be a mapping."
        )

    # Support both top-level and nested under 'job' key
    job_data = data.get("job", data)

    reqs = job_data.get("requirements", {})

    return JobDescription(
        title=job_data.get("title", "Unknown Position"),
        company=job_data.get("company", "Unknown Company"),
        url=job_data.get("url"),
        source=source if source in ("url", "file", "stdin") else "file",
        requirements=JobRequirements(
            required_skills=reqs.get("required_skills", []),
            preferred_skills=reqs.get("preferred_skills", []),
            experience_years=reqs.get("experience_years"),
            education=reqs.get("education"),
        ),
        raw_text=job_data.get("raw_text", text),
    )
