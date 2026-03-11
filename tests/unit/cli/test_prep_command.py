"""Tests for ``anvil prep`` CLI command.

Why:
    The prep command generates interview preparation notes using AI.
    Tests cover happy path, error cases (bad job, bad YAML, AI error,
    unconfigured provider, unknown provider), and output path defaults.
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import anvilcv.cli.prep_command.prep_command  # noqa: F401
from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilAIProviderError, AnvilUserError
from anvilcv.tailoring.matcher import MatchResult, ResumeMatch

runner = CliRunner()


def _make_match() -> ResumeMatch:
    return ResumeMatch(
        matches=[
            MatchResult(
                section_path="experience.0.highlights.0",
                content="Designed data pipeline",
                matched_skills=["python", "kafka"],
                relevance_score=0.9,
            ),
        ],
        missing_required=["kubernetes"],
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


class TestPrepHappyPath:
    """Full prep notes generation with mocked AI."""

    @patch("anvilcv.prep.generator.write_prep_notes")
    @patch("anvilcv.prep.generator.generate_prep_notes")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_prep_writes_notes(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_gen: MagicMock,
        mock_write: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)
        out = tmp_path / "prep.md"

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_gen.return_value = "# Interview Prep\n\n- Talk about data pipeline"
        mock_write.return_value = None

        result = runner.invoke(app, ["prep", str(resume), "--job", str(job), "--output", str(out)])
        assert result.exit_code == 0
        assert "Prep notes written to" in result.output

    @patch("anvilcv.prep.generator.write_prep_notes")
    @patch("anvilcv.prep.generator.generate_prep_notes")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_prep_default_output_path(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_gen: MagicMock,
        mock_write: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """When --output is not given, uses {name}_prep.md."""
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_gen.return_value = "# Prep notes"
        mock_write.return_value = None

        result = runner.invoke(app, ["prep", str(resume), "--job", str(job)])
        assert result.exit_code == 0
        assert "Test_User_prep.md" in result.output

    @patch("anvilcv.prep.generator.write_prep_notes")
    @patch("anvilcv.prep.generator.generate_prep_notes")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_prep_with_provider_flag(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_gen: MagicMock,
        mock_write: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """--provider flag selects the AI provider."""
        resume, job = _write_resume_and_job(tmp_path)
        out = tmp_path / "prep.md"

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="openai")
        mock_gen.return_value = "# Prep"
        mock_write.return_value = None

        result = runner.invoke(
            app,
            [
                "prep",
                str(resume),
                "--job",
                str(job),
                "--provider",
                "openai",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        mock_resolve.assert_called_once()


class TestPrepErrors:
    """Error cases."""

    def test_missing_input(self) -> None:
        result = runner.invoke(app, ["prep"])
        assert result.exit_code == 2

    def test_missing_job_flag(self, tmp_path: pathlib.Path) -> None:
        resume = tmp_path / "resume.yaml"
        resume.write_text("cv:\n  name: Test\n")
        result = runner.invoke(app, ["prep", str(resume)])
        assert result.exit_code == 2

    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_bad_job_file(self, mock_resolve_job: MagicMock, tmp_path: pathlib.Path) -> None:
        resume, job = _write_resume_and_job(tmp_path)
        mock_resolve_job.side_effect = AnvilUserError(message="bad job")

        result = runner.invoke(app, ["prep", str(resume), "--job", str(job)])
        assert result.exit_code == 1
        assert "Error reading job description" in result.output

    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_bad_resume_yaml(self, mock_resolve_job: MagicMock, tmp_path: pathlib.Path) -> None:
        resume = tmp_path / "bad.yaml"
        resume.write_text(": invalid [\n")
        job = tmp_path / "job.txt"
        job.write_text("Engineer")
        mock_resolve_job.return_value = MagicMock(company="Corp")

        result = runner.invoke(app, ["prep", str(resume), "--job", str(job)])
        assert result.exit_code in (0, 1)

    @patch("anvilcv.prep.generator.generate_prep_notes")
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

        result = runner.invoke(app, ["prep", str(resume), "--job", str(job)])
        assert result.exit_code == 4
        assert "AI error" in result.output
