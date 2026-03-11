"""Tier 2 golden-set regression tests for the tailor feature.

Why:
    Tier 1 tests (unit/tailoring/) use mocked APIs and verify structural
    correctness. Tier 2 tests hit live AI APIs to verify that tailored output
    actually contains relevant, specific, non-fabricated content. This catches
    quality regressions that structural tests cannot detect — e.g., a model
    update producing generic bullets or hallucinating experience.

    Run with: pytest tests/golden/test_golden_tailor.py --run-golden -p no:numprocesses
    Requires: ANTHROPIC_API_KEY and/or OPENAI_API_KEY environment variables.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest
from ruamel.yaml import YAML

# Add tests/ to path so golden package is importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from anvilcv.schema.job_description import JobDescription, JobRequirements  # noqa: E402
from anvilcv.tailoring.matcher import match_resume_to_job  # noqa: E402
from anvilcv.tailoring.rewriter import rewrite_top_bullets  # noqa: E402
from golden.conftest import get_provider, load_case_data, provider_available  # noqa: E402
from golden.evaluator import evaluate_output_sync  # noqa: E402

GOLDEN_DIR = pathlib.Path(__file__).parent
TAILOR_DIR = GOLDEN_DIR / "tailor"

yaml = YAML()
yaml.preserve_quotes = True

# Discover all tailor cases
TAILOR_CASES = sorted(
    d.name for d in TAILOR_DIR.iterdir() if d.is_dir() and d.name.startswith("case_")
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


def _run_tailor(resume_data: dict, job: JobDescription, provider) -> str:
    """Run the tailor pipeline and return the variant YAML as string."""
    match = match_resume_to_job(resume_data, job)

    # Get bullets to rewrite
    bullets_to_rewrite = [
        (m.section_path, m.content) for m in match.matches if m.relevance_score > 0
    ][:10]

    if not bullets_to_rewrite:
        # If no matches found, use all experience bullets
        bullets_to_rewrite = [(m.section_path, m.content) for m in match.matches][:10]

    changes = asyncio.run(
        rewrite_top_bullets(provider, bullets_to_rewrite, job, match, max_rewrites=10)
    )

    # Build variant output as YAML string
    import copy
    import io

    data = copy.deepcopy(resume_data)
    from anvilcv.tailoring.variant_writer import _apply_change

    for section_path, new_content in changes.items():
        _apply_change(data, section_path, new_content)

    buf = io.StringIO()
    yaml.dump(data, buf)
    return buf.getvalue()


@pytest.mark.golden
@pytest.mark.parametrize("case_name", TAILOR_CASES)
@pytest.mark.parametrize("provider_name", PROVIDERS)
def test_tailor_golden(case_name: str, provider_name: str) -> None:
    """Run tailor on a golden-set case and evaluate against rubric.

    Asserts the evaluation score meets the minimum threshold (50/100).
    """
    if not provider_available(provider_name):
        pytest.skip(f"{provider_name} provider not available")

    provider = get_provider(provider_name)
    assert provider is not None

    resume_data, job_data, rubric = load_case_data("tailor", case_name)
    job = _build_job_description(job_data)

    # Run tailor pipeline
    output = _run_tailor(resume_data, job, provider)

    # Evaluate against rubric
    result = evaluate_output_sync(
        output=output,
        rubric=rubric,
        case_name=case_name,
        feature="tailor",
        provider=provider_name,
    )

    # Log detailed results for debugging
    print(f"\n{'=' * 60}")
    print(f"TAILOR | {case_name} | {provider_name}")
    print(f"Total Score: {result.total_score:.1f}/100")
    for cr in result.criterion_results:
        print(f"  [{cr.criterion_type}] {cr.name}: {cr.score:.2f} (w={cr.weight})")
        print(f"    Evidence: {cr.evidence}")
    print(f"{'=' * 60}\n")

    assert result.total_score >= MIN_SCORE, (
        f"Tailor golden-set {case_name} ({provider_name}) scored "
        f"{result.total_score:.1f}/100, minimum is {MIN_SCORE}/100.\n"
        f"Criterion details:\n"
        + "\n".join(
            f"  {cr.name}: {cr.score:.2f} — {cr.evidence}" for cr in result.criterion_results
        )
    )
