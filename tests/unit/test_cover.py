"""Tests for cover letter generation.

Why:
    Tier 1 structural tests with mocked AI providers verify that the cover
    letter generator produces valid output and writes files correctly.
"""

import asyncio
import pathlib
from unittest.mock import AsyncMock, MagicMock

from anvilcv.ai.prompts.cover_letter.common import build_cover_letter_prompt
from anvilcv.ai.provider import GenerationResponse
from anvilcv.cover.generator import generate_cover_letter, write_cover_letter
from anvilcv.schema.job_description import JobDescription, JobRequirements
from anvilcv.tailoring.matcher import ResumeMatch


def _make_job() -> JobDescription:
    return JobDescription(
        title="Senior Backend Engineer",
        company="Acme Corp",
        requirements=JobRequirements(
            required_skills=["Python", "AWS", "PostgreSQL"],
            preferred_skills=["Go", "Kubernetes"],
        ),
        raw_text="Senior Backend Engineer at Acme Corp...",
    )


def _make_match() -> ResumeMatch:
    return ResumeMatch(
        matches=[],
        resume_skills={"Python", "AWS"},
        missing_required=["PostgreSQL"],
        missing_preferred=["Go", "Kubernetes"],
    )


SAMPLE_RESUME = {
    "cv": {
        "name": "Jane Developer",
        "sections": {
            "experience": [
                {
                    "company": "TechCo",
                    "position": "Senior Engineer",
                    "start_date": "2021-06",
                    "end_date": "present",
                    "highlights": [
                        "Built real-time pipeline processing 500K events/sec",
                    ],
                },
            ],
        },
    }
}


class TestBuildCoverLetterPrompt:
    def test_returns_tuple(self):
        job = _make_job()
        result = build_cover_letter_prompt(
            "resume text", job, ["Python"], ["Go"]
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_system_prompt_mentions_cover_letter(self):
        job = _make_job()
        system, _ = build_cover_letter_prompt(
            "resume text", job, ["Python"], ["Go"]
        )
        assert "cover letter" in system.lower()

    def test_user_prompt_includes_company(self):
        job = _make_job()
        _, user = build_cover_letter_prompt(
            "resume text", job, ["Python"], ["Go"]
        )
        assert "Acme Corp" in user

    def test_user_prompt_non_generic(self):
        job = _make_job()
        _, user = build_cover_letter_prompt(
            "resume text", job, ["Python"], ["Go"]
        )
        assert "Do NOT fabricate" in user


class TestGenerateCoverLetter:
    def test_generates_content(self):
        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=GenerationResponse(
                content=(
                    "Dear Hiring Manager,\n\n"
                    "I am excited to apply for the Senior Backend Engineer "
                    "position at Acme Corp..."
                ),
                model="test-model",
                provider="test",
                input_tokens=100,
                output_tokens=80,
            )
        )

        result = asyncio.run(
            generate_cover_letter(
                provider, SAMPLE_RESUME, _make_job(), _make_match()
            )
        )
        assert "Acme Corp" in result
        assert isinstance(result, str)


class TestWriteCoverLetter:
    def test_writes_file(self, tmp_path: pathlib.Path):
        output = tmp_path / "cover.md"
        result = write_cover_letter(
            "Dear Hiring Manager,\n\nContent here.", output
        )
        assert result == output
        assert output.exists()
        assert "Dear Hiring Manager" in output.read_text()

    def test_creates_parent_dirs(self, tmp_path: pathlib.Path):
        output = tmp_path / "nested" / "dir" / "cover.md"
        write_cover_letter("content", output)
        assert output.exists()
