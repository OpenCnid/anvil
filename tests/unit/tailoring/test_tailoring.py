"""Tests for AI tailoring pipeline.

Why:
    Tier 1 structural tests: output parses as YAML, conforms to schema,
    provenance metadata present. All AI calls are mocked.
"""

import asyncio
import pathlib
from unittest.mock import AsyncMock, MagicMock

from anvilcv.ai.provider import GenerationResponse
from anvilcv.schema.job_description import JobDescription, JobRequirements
from anvilcv.tailoring.matcher import ResumeMatch, match_resume_to_job
from anvilcv.tailoring.rewriter import build_rewrite_prompt, rewrite_bullet
from anvilcv.tailoring.variant_writer import write_variant

# --- Fixtures ---


def _sample_resume() -> dict:
    return {
        "cv": {
            "name": "John Doe",
            "sections": {
                "experience": [
                    {
                        "company": "Acme Corp",
                        "position": "Software Engineer",
                        "highlights": [
                            "Built scalable Python microservices",
                            "Led migration to cloud infrastructure",
                            "Improved API response time by 40%",
                        ],
                    },
                ],
                "skills": [
                    {"label": "Languages", "details": "Python, Go, TypeScript"},
                ],
            },
        },
    }


def _sample_job() -> JobDescription:
    return JobDescription(
        title="Senior SRE",
        company="TechCo",
        requirements=JobRequirements(
            required_skills=["Python", "Kubernetes", "Terraform"],
            preferred_skills=["Docker", "AWS"],
            experience_years=5,
        ),
        raw_text=(
            "We are looking for a Senior SRE with Python, "
            "Kubernetes, and Terraform experience."
        ),
    )


# --- Matcher ---


class TestMatcher:
    def test_matches_relevant_bullets(self):
        resume = _sample_resume()
        job = _sample_job()
        match = match_resume_to_job(resume, job)

        assert isinstance(match, ResumeMatch)
        assert len(match.matches) > 0
        # Python bullet should match
        python_matches = [
            m for m in match.matches if "Python" in m.matched_skills
        ]
        assert len(python_matches) > 0

    def test_identifies_missing_skills(self):
        resume = _sample_resume()
        job = _sample_job()
        match = match_resume_to_job(resume, job)

        # Terraform and Kubernetes aren't in the resume bullets
        assert "Terraform" in match.missing_required
        assert "Kubernetes" in match.missing_required

    def test_extracts_resume_skills(self):
        resume = _sample_resume()
        job = _sample_job()
        match = match_resume_to_job(resume, job)

        assert "Python" in match.resume_skills

    def test_empty_sections(self):
        resume = {"cv": {"name": "Test", "sections": {}}}
        job = _sample_job()
        match = match_resume_to_job(resume, job)
        assert len(match.matches) == 0

    def test_sorted_by_relevance(self):
        resume = _sample_resume()
        job = _sample_job()
        match = match_resume_to_job(resume, job)

        if len(match.matches) >= 2:
            scores = [m.relevance_score for m in match.matches]
            assert scores == sorted(scores, reverse=True)


# --- Rewriter ---


class TestRewriter:
    def test_build_rewrite_prompt(self):
        job = _sample_job()
        match = ResumeMatch(
            missing_required=["Terraform", "Kubernetes"],
            job_required_skills=["Python", "Kubernetes", "Terraform"],
        )
        prompt = build_rewrite_prompt(
            "Built scalable Python microservices",
            job,
            match,
        )
        assert "Python" in prompt
        assert "TechCo" in prompt
        assert "Terraform" in prompt

    def test_rewrite_bullet_success(self):
        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=GenerationResponse(
                content="Built and deployed Python microservices on Kubernetes",
                model="test",
                provider="test",
            )
        )

        job = _sample_job()
        match = ResumeMatch(missing_required=["Kubernetes"])

        result = asyncio.run(
            rewrite_bullet(
                provider,
                "Built scalable Python microservices",
                job,
                match,
            )
        )
        assert "Kubernetes" in result

    def test_rewrite_bullet_fallback_on_error(self):
        provider = MagicMock()
        provider.generate = AsyncMock(side_effect=Exception("API error"))

        job = _sample_job()
        match = ResumeMatch()

        result = asyncio.run(
            rewrite_bullet(
                provider,
                "Original bullet",
                job,
                match,
            )
        )
        assert result == "Original bullet"

    def test_rewrite_bullet_rejects_too_long(self):
        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=GenerationResponse(
                content="x" * 10000,  # Way too long
                model="test",
                provider="test",
            )
        )

        job = _sample_job()
        match = ResumeMatch()

        result = asyncio.run(
            rewrite_bullet(provider, "Short bullet", job, match)
        )
        assert result == "Short bullet"


# --- Variant Writer ---


class TestVariantWriter:
    def test_writes_variant_with_provenance(self, tmp_path: pathlib.Path):
        resume = _sample_resume()
        changes = {"experience.0.highlights.0": "Rewritten bullet"}
        output = tmp_path / "variant.yaml"

        result = write_variant(
            original_data=resume,
            changes=changes,
            source_path="./cv.yaml",
            job_path=".anvil/jobs/acme.yaml",
            provider_name="anthropic",
            model_name="claude-sonnet-4-20250514",
            output_path=output,
        )

        assert result.exists()

        from ruamel.yaml import YAML

        yaml = YAML()
        with open(result) as f:
            data = yaml.load(f)

        # Check provenance
        assert "variant" in data
        assert data["variant"]["provider"] == "anthropic"
        assert data["variant"]["source"] == "./cv.yaml"
        assert len(data["variant"]["changes"]) == 1

    def test_does_not_modify_original(self, tmp_path: pathlib.Path):
        import copy

        resume = _sample_resume()
        original_copy = copy.deepcopy(resume)
        output = tmp_path / "variant.yaml"

        write_variant(
            original_data=resume,
            changes={"experience.0.highlights.0": "Changed"},
            source_path="./cv.yaml",
            job_path=None,
            provider_name="test",
            model_name="test",
            output_path=output,
        )

        # Original should be unchanged
        assert resume == original_copy

    def test_creates_output_directory(self, tmp_path: pathlib.Path):
        resume = _sample_resume()
        output = tmp_path / "nested" / "dir" / "variant.yaml"

        write_variant(
            original_data=resume,
            changes={},
            source_path="./cv.yaml",
            job_path=None,
            provider_name="test",
            model_name="test",
            output_path=output,
        )

        assert output.exists()
