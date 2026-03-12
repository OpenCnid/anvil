"""Tier 2 golden-set regression tests for the interview prep feature.

Why:
    Interview prep notes must be specific to the candidate's actual projects
    and matched to job requirements. Generic advice (e.g., "talk about your
    experience") is useless. Tier 2 tests verify that prep output references
    real projects, contains structured talking points, and doesn't fabricate
    experiences — things that structural Tier 1 tests can't catch.

    Run with: pytest tests/golden/test_golden_prep.py --run-golden -p no:numprocesses
    Requires: ANTHROPIC_API_KEY and/or OPENAI_API_KEY environment variables.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest

# Add tests/ to path so golden package is importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from anvilcv.prep.generator import generate_prep_notes  # noqa: E402
from anvilcv.schema.job_description import JobDescription, JobRequirements  # noqa: E402
from anvilcv.tailoring.matcher import match_resume_to_job  # noqa: E402
from golden.conftest import get_provider, load_case_data, provider_available  # noqa: E402
from golden.evaluator import evaluate_output_sync  # noqa: E402

GOLDEN_DIR = pathlib.Path(__file__).parent
PREP_DIR = GOLDEN_DIR / "prep"

# Discover all prep cases
PREP_CASES = sorted(d.name for d in PREP_DIR.iterdir() if d.is_dir() and d.name.startswith("case_"))

PROVIDERS = ["anthropic", "openai"]

MIN_SCORE = 50  # Minimum passing score per spec


def _build_job_description(job_data: dict) -> JobDescription:
    """Build a JobDescription from loaded YAML data."""
    reqs = job_data.get("requirements", {})
    return JobDescription(
        title=job_data["title"],
        company=job_data["company"],
        url=job_data.get("url"),
        source="file",
        requirements=JobRequirements(
            required_skills=reqs.get("required_skills", []),
            preferred_skills=reqs.get("preferred_skills", []),
            experience_years=reqs.get("experience_years"),
            education=reqs.get("education"),
        ),
        raw_text=job_data.get("raw_text", ""),
    )


@pytest.mark.golden
@pytest.mark.parametrize("case_name", PREP_CASES)
@pytest.mark.parametrize("provider_name", PROVIDERS)
def test_prep_golden(case_name: str, provider_name: str) -> None:
    """Run interview prep generation and evaluate against rubric.

    Asserts the evaluation score meets the minimum threshold (50/100).
    """
    if not provider_available(provider_name):
        pytest.skip(f"{provider_name} provider not available")

    provider = get_provider(provider_name)
    assert provider is not None

    resume_data, job_data, rubric = load_case_data("prep", case_name)
    job = _build_job_description(job_data)
    match = match_resume_to_job(resume_data, job)

    # Generate prep notes
    output = asyncio.run(generate_prep_notes(provider, resume_data, job, match))

    # Evaluate against rubric
    result = evaluate_output_sync(
        output=output,
        rubric=rubric,
        case_name=case_name,
        feature="prep",
        provider=provider_name,
    )

    # Log detailed results for debugging
    print(f"\n{'=' * 60}")
    print(f"PREP | {case_name} | {provider_name}")
    print(f"Total Score: {result.total_score:.1f}/100")
    for cr in result.criterion_results:
        print(f"  [{cr.criterion_type}] {cr.name}: {cr.score:.2f} (w={cr.weight})")
        print(f"    Evidence: {cr.evidence}")
    print(f"{'=' * 60}\n")

    assert result.total_score >= MIN_SCORE, (
        f"Prep golden-set {case_name} ({provider_name}) scored "
        f"{result.total_score:.1f}/100, minimum is {MIN_SCORE}/100.\n"
        f"Criterion details:\n"
        + "\n".join(
            f"  {cr.name}: {cr.score:.2f} — {cr.evidence}" for cr in result.criterion_results
        )
    )
