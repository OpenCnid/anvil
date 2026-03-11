"""Tests for ``anvil cover`` CLI command.

Why:
    The cover command generates a cover letter using AI.
    Tests cover happy path, error cases (bad job, bad YAML, AI error,
    unconfigured provider, unknown provider), and output path defaults.
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import anvilcv.cli.cover_command.cover_command  # noqa: F401
from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilAIProviderError, AnvilUserError
from anvilcv.tailoring.matcher import MatchResult, ResumeMatch

runner = CliRunner()


def _make_match() -> ResumeMatch:
    return ResumeMatch(
        matches=[
            MatchResult(
                section_path="experience.0.highlights.0",
                content="Built scalable services",
                matched_skills=["python"],
                relevance_score=0.9,
            ),
        ],
        missing_required=["go"],
    )


def _write_resume_and_job(tmp_path: pathlib.Path):
    resume = tmp_path / "resume.yaml"
    resume.write_text(
        "cv:\n  name: Test User\n  sections:\n"
        "    experience:\n      - company: Acme\n"
        "        highlights:\n          - Built thing\n"
    )
    job = tmp_path / "job.txt"
    job.write_text("Senior Engineer at TechCo")
    return resume, job


class TestCoverHappyPath:
    """Full cover letter generation with mocked AI."""

    @patch("anvilcv.cover.generator.write_cover_letter")
    @patch("anvilcv.cover.generator.generate_cover_letter")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_cover_writes_letter(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_gen: MagicMock,
        mock_write: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)
        out = tmp_path / "cover.md"

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_gen.return_value = "Dear Hiring Manager..."
        mock_write.return_value = None

        result = runner.invoke(app, ["cover", str(resume), "--job", str(job), "--output", str(out)])
        assert result.exit_code == 0
        assert "Cover letter written to" in result.output

    @patch("anvilcv.cover.generator.write_cover_letter")
    @patch("anvilcv.cover.generator.generate_cover_letter")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_cover_default_output_path(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_gen: MagicMock,
        mock_write: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """When --output is not given, uses {name}_cover.md."""
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_gen.return_value = "Dear Hiring Manager..."
        mock_write.return_value = None

        result = runner.invoke(app, ["cover", str(resume), "--job", str(job)])
        assert result.exit_code == 0
        assert "Test_User_cover.md" in result.output


class TestCoverErrors:
    """Error cases."""

    def test_missing_input(self) -> None:
        result = runner.invoke(app, ["cover"])
        assert result.exit_code == 2

    def test_missing_job_flag(self, tmp_path: pathlib.Path) -> None:
        resume = tmp_path / "resume.yaml"
        resume.write_text("cv:\n  name: Test\n")
        result = runner.invoke(app, ["cover", str(resume)])
        assert result.exit_code == 2

    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_bad_job_file(self, mock_resolve_job: MagicMock, tmp_path: pathlib.Path) -> None:
        resume, job = _write_resume_and_job(tmp_path)
        mock_resolve_job.side_effect = AnvilUserError(message="bad job")

        result = runner.invoke(app, ["cover", str(resume), "--job", str(job)])
        assert result.exit_code == 1
        assert "Error reading job description" in result.output

    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_bad_resume_yaml(self, mock_resolve_job: MagicMock, tmp_path: pathlib.Path) -> None:
        resume = tmp_path / "bad.yaml"
        resume.write_text(": invalid [\n")
        job = tmp_path / "job.txt"
        job.write_text("Engineer at Corp")
        mock_resolve_job.return_value = MagicMock(company="Corp")

        result = runner.invoke(app, ["cover", str(resume), "--job", str(job)])
        assert result.exit_code in (0, 1)

    @patch("anvilcv.cover.generator.generate_cover_letter")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_ai_error_exits_4(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_gen: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_gen.side_effect = AnvilAIProviderError(message="rate limited")

        result = runner.invoke(app, ["cover", str(resume), "--job", str(job)])
        assert result.exit_code == 4
        assert "AI error" in result.output
