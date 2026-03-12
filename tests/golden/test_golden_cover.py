"""Tier 2 golden-set regression tests for the cover letter feature.

Why:
    Cover letter quality requires live API validation. Tier 1 tests verify
    structure (returns a string, mentions company name). Tier 2 tests check
    that the cover letter is specific to the candidate's actual experience,
    references real projects and metrics, and doesn't fabricate skills or
    achievements. A model update could silently produce generic letters that
    pass structural tests but fail real-world use.

    Run with: pytest tests/golden/test_golden_cover.py --run-golden -p no:numprocesses
    Requires: ANTHROPIC_API_KEY and/or OPENAI_API_KEY environment variables.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest

# Add tests/ to path so golden package is importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from anvilcv.cover.generator import generate_cover_letter  # noqa: E402
from anvilcv.schema.job_description import JobDescription, JobRequirements  # noqa: E402
from anvilcv.tailoring.matcher import match_resume_to_job  # noqa: E402
from golden.conftest import get_provider, load_case_data, provider_available  # noqa: E402
from golden.evaluator import evaluate_output_sync  # noqa: E402

GOLDEN_DIR = pathlib.Path(__file__).parent
COVER_DIR = GOLDEN_DIR / "cover"

# Discover all cover cases
COVER_CASES = sorted(
    d.name for d in COVER_DIR.iterdir() if d.is_dir() and d.name.startswith("case_")
)

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
@pytest.mark.parametrize("case_name", COVER_CASES)
@pytest.mark.parametrize("provider_name", PROVIDERS)
def test_cover_golden(case_name: str, provider_name: str) -> None:
    """Run cover letter generation and evaluate against rubric.

    Asserts the evaluation score meets the minimum threshold (50/100).
    """
    if not provider_available(provider_name):
        pytest.skip(f"{provider_name} provider not available")

    provider = get_provider(provider_name)
    assert provider is not None

    resume_data, job_data, rubric = load_case_data("cover", case_name)
    job = _build_job_description(job_data)
    match = match_resume_to_job(resume_data, job)

    # Generate cover letter
    output = asyncio.run(generate_cover_letter(provider, resume_data, job, match))

    # Evaluate against rubric
    result = evaluate_output_sync(
        output=output,
        rubric=rubric,
        case_name=case_name,
        feature="cover",
        provider=provider_name,
    )

    # Log detailed results for debugging
    print(f"\n{'=' * 60}")
    print(f"COVER | {case_name} | {provider_name}")
    print(f"Total Score: {result.total_score:.1f}/100")
    for cr in result.criterion_results:
        print(f"  [{cr.criterion_type}] {cr.name}: {cr.score:.2f} (w={cr.weight})")
        print(f"    Evidence: {cr.evidence}")
    print(f"{'=' * 60}\n")

    assert result.total_score >= MIN_SCORE, (
        f"Cover golden-set {case_name} ({provider_name}) scored "
        f"{result.total_score:.1f}/100, minimum is {MIN_SCORE}/100.\n"
        f"Criterion details:\n"
        + "\n".join(
            f"  {cr.name}: {cr.score:.2f} — {cr.evidence}" for cr in result.criterion_results
        )
    )
