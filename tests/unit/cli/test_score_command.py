"""Tests for ``anvil score`` CLI command.

Why:
    The score command checks ATS compatibility of a resume file.
    Tests cover happy-path text/JSON output, --job flag, --output flag,
    --verbose flag, error cases, and the _print_text_report helper.
"""

from __future__ import annotations

import json
import pathlib
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import anvilcv.cli.score_command.score_command  # noqa: F401
from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilUserError
from anvilcv.schema.score_report import (
    Check,
    KeywordMatchSection,
    Recommendation,
    ScoreReport,
    SectionScore,
)

runner = CliRunner()


def _make_report(
    overall: int = 85,
    keyword_match: KeywordMatchSection | None = None,
    recommendations: list[Recommendation] | None = None,
) -> ScoreReport:
    """Build a minimal ScoreReport for testing."""
    return ScoreReport(
        file="test.pdf",
        overall_score=overall,
        parsability=SectionScore(
            score=90,
            checks=[
                Check(name="PDF text layer", status="pass"),
                Check(
                    name="Font embedding",
                    status="warn",
                    detail="1 font not embedded",
                    confidence="opinionated_heuristic",
                ),
            ],
        ),
        structure=SectionScore(
            score=80,
            checks=[
                Check(name="Section headings", status="pass"),
                Check(name="Bullet consistency", status="fail", detail="Inconsistent bullets"),
            ],
        ),
        keyword_match=keyword_match,
        recommendations=recommendations or [],
    )


class TestScoreHappyPath:
    """Score command with valid inputs."""

    @patch("anvilcv.scoring.ats_scorer.score_document")
    def test_score_text_output(self, mock_score: MagicMock, tmp_path: pathlib.Path) -> None:
        """Default text format prints a human-readable report."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 0
        assert "ATS Compatibility Report" in result.output
        assert "Score: 85/100" in result.output

    @patch("anvilcv.scoring.ats_scorer.score_document")
    def test_score_json_output(self, mock_score: MagicMock, tmp_path: pathlib.Path) -> None:
        """--format json prints valid JSON."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["overall_score"] == 85

    @patch("anvilcv.scoring.ats_scorer.score_document")
    def test_score_json_to_file(self, mock_score: MagicMock, tmp_path: pathlib.Path) -> None:
        """--format json --output writes JSON to a file."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        out = tmp_path / "report.json"
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--format", "json", "--output", str(out)])
        assert result.exit_code == 0
        assert "Report written to" in result.output
        data = json.loads(out.read_text())
        assert data["overall_score"] == 85

    @patch("anvilcv.scoring.ats_scorer.score_document")
    def test_score_text_to_file(self, mock_score: MagicMock, tmp_path: pathlib.Path) -> None:
        """Text output --output writes to a file."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        out = tmp_path / "report.txt"
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--output", str(out)])
        assert result.exit_code == 0
        assert "Report written to" in result.output
        text = out.read_text()
        assert "ATS Compatibility Report" in text

    @patch("anvilcv.scoring.ats_scorer.score_document")
    def test_score_verbose(self, mock_score: MagicMock, tmp_path: pathlib.Path) -> None:
        """--verbose shows confidence levels."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--verbose"])
        assert result.exit_code == 0
        assert "opinionated heuristic" in result.output


class TestScoreWithJob:
    """Score command with --job flag."""

    @patch("anvilcv.scoring.ats_scorer.score_document")
    @patch("anvilcv.tailoring.job_parser.parse_job_from_file")
    def test_score_with_job(
        self,
        mock_parse_job: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """--job passes parsed job description to score_document."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Senior Python Developer at Acme Corp")

        mock_job = MagicMock()
        mock_parse_job.return_value = mock_job
        mock_score.return_value = _make_report(
            keyword_match=KeywordMatchSection(
                score=70,
                job_keywords=["python", "django"],
                matched=["python"],
                missing=["django"],
            ),
        )

        result = runner.invoke(app, ["score", str(pdf), "--job", str(job_file)])
        assert result.exit_code == 0
        mock_score.assert_called_once_with(pdf, job=mock_job)
        assert "Keywords:" in result.output
        assert "Matched: python" in result.output
        assert "Missing: django" in result.output

    @patch("anvilcv.tailoring.job_parser.parse_job_from_file")
    def test_score_job_parse_error(self, mock_parse_job: MagicMock, tmp_path: pathlib.Path) -> None:
        """Bad --job file exits with code 1."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        job_file = tmp_path / "bad_job.txt"
        job_file.write_text("invalid")
        mock_parse_job.side_effect = AnvilUserError(message="bad job file")

        result = runner.invoke(app, ["score", str(pdf), "--job", str(job_file)])
        assert result.exit_code == 1
        assert "Error reading job description" in result.output


class TestScoreErrors:
    """Error cases for the score command."""

    def test_score_missing_input(self) -> None:
        """No input argument exits with code 2 (usage error)."""
        result = runner.invoke(app, ["score"])
        assert result.exit_code == 2

    def test_score_nonexistent_file(self, tmp_path: pathlib.Path) -> None:
        """Non-existent file exits with code 2 (Typer validation)."""
        result = runner.invoke(app, ["score", str(tmp_path / "nope.pdf")])
        assert result.exit_code == 2

    @patch("anvilcv.scoring.ats_scorer.score_document")
    def test_score_document_error(self, mock_score: MagicMock, tmp_path: pathlib.Path) -> None:
        """AnvilUserError from score_document exits with code 1."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_score.side_effect = AnvilUserError(message="corrupt PDF")

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 1
        assert "Error: corrupt PDF" in result.output


class TestScoreReportFormatting:
    """Test _print_text_report and _status_icon helpers."""

    def test_recommendations_in_text_report(self, tmp_path: pathlib.Path) -> None:
        """Recommendations section appears in text output."""
        from anvilcv.cli.score_command.score_command import _print_text_report

        report = _make_report(
            recommendations=[
                Recommendation(priority="high", message="Add more keywords"),
                Recommendation(priority="low", message="Consider reordering"),
            ],
        )
        # Capture via output file
        out = tmp_path / "report.txt"
        _print_text_report(report, output=out)
        text = out.read_text()
        assert "[HIGH] Add more keywords" in text
        assert "[LOW] Consider reordering" in text

    def test_status_icon_values(self) -> None:
        """_status_icon returns expected icons."""
        from anvilcv.cli.score_command.score_command import _status_icon

        assert _status_icon("pass") == "[PASS]"
        assert _status_icon("fail") == "[FAIL]"
        assert _status_icon("warn") == "[WARN]"
        assert _status_icon("unknown") == "[????]"
