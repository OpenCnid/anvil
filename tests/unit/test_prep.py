"""Tests for interview prep generation.

Why:
    Tier 1 structural tests with mocked AI providers verify that the prep
    generator produces valid output, handles edge cases, and writes files.
"""

import asyncio
import pathlib
from unittest.mock import AsyncMock, MagicMock

from anvilcv.ai.prompts.interview_prep.common import build_prep_prompt
from anvilcv.ai.provider import GenerationResponse
from anvilcv.prep.generator import (
    extract_resume_text,
    generate_prep_notes,
    write_prep_notes,
)
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
            "skills": [
                {"label": "Languages", "details": "Python, Go, Rust"},
            ],
        },
    }
}


class TestExtractResumeText:
    def test_extracts_name(self):
        text = extract_resume_text(SAMPLE_RESUME)
        assert "Jane Developer" in text

    def test_extracts_experience(self):
        text = extract_resume_text(SAMPLE_RESUME)
        assert "TechCo" in text
        assert "Senior Engineer" in text
        assert "500K events/sec" in text

    def test_extracts_skills(self):
        text = extract_resume_text(SAMPLE_RESUME)
        assert "Languages" in text
        assert "Python, Go, Rust" in text

    def test_handles_empty_resume(self):
        text = extract_resume_text({"cv": {"sections": {}}})
        assert isinstance(text, str)


class TestBuildPrepPrompt:
    def test_returns_tuple(self):
        job = _make_job()
        result = build_prep_prompt("resume text", job, ["Python"], ["Go"])
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_system_prompt_mentions_interview(self):
        job = _make_job()
        system, _ = build_prep_prompt("resume text", job, ["Python"], ["Go"])
        assert "interview" in system.lower()

    def test_user_prompt_includes_job(self):
        job = _make_job()
        _, user = build_prep_prompt("resume text", job, ["Python"], ["Go"])
        assert "Acme Corp" in user
        assert "Senior Backend Engineer" in user

    def test_user_prompt_includes_skills(self):
        job = _make_job()
        _, user = build_prep_prompt("resume text", job, ["Python"], ["Go"])
        assert "Python" in user


class TestGeneratePrepNotes:
    def test_generates_content(self):
        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=GenerationResponse(
                content="## TechCo\n\nIf they ask about backend work...",
                model="test-model",
                provider="test",
                input_tokens=100,
                output_tokens=50,
            )
        )

        result = asyncio.run(
            generate_prep_notes(provider, SAMPLE_RESUME, _make_job(), _make_match())
        )
        assert "TechCo" in result
        assert isinstance(result, str)


class TestWritePrepNotes:
    def test_writes_file(self, tmp_path: pathlib.Path):
        output = tmp_path / "prep.md"
        result = write_prep_notes("# Prep Notes\n\nContent here.", output)
        assert result == output
        assert output.exists()
        assert "Prep Notes" in output.read_text()

    def test_creates_parent_dirs(self, tmp_path: pathlib.Path):
        output = tmp_path / "nested" / "dir" / "prep.md"
        write_prep_notes("content", output)
        assert output.exists()
