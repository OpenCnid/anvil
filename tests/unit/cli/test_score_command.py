"""Tests for ``anvil score`` CLI command.

Why:
    The score command checks ATS compatibility of a resume file.
    Tests cover happy-path text/JSON output, --job flag, --output flag,
    --verbose flag, error cases, PDF extraction failure/partial handling,
    and the _print_text_report helper.
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
from anvilcv.scoring.text_extractor import ExtractedDocument

runner = CliRunner()

# Shared mock targets for the new extraction-then-score flow
_EXTRACT = "anvilcv.scoring.text_extractor.extract_text"
_SCORE_DOC = "anvilcv.scoring.ats_scorer.score_extracted_document"


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


def _make_doc(
    full_text: str = "John Doe\nExperience\nBuilt things",
    source_type: str = "pdf",
    page_count: int = 1,
    image_page_count: int = 0,
) -> ExtractedDocument:
    """Build a minimal ExtractedDocument for testing."""
    return ExtractedDocument(
        full_text=full_text,
        source_type=source_type,
        page_count=page_count,
        image_page_count=image_page_count,
    )


class TestScoreHappyPath:
    """Score command with valid inputs."""

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_score_text_output(
        self, mock_extract: MagicMock, mock_score: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """Default text format prints a human-readable report."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 0
        assert "ATS Compatibility Report" in result.output
        assert "Score: 85/100" in result.output

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_score_json_output(
        self, mock_extract: MagicMock, mock_score: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """--format json prints valid JSON."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["overall_score"] == 85

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_score_json_to_file(
        self, mock_extract: MagicMock, mock_score: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """--format json --output writes JSON to a file."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        out = tmp_path / "report.json"
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--format", "json", "--output", str(out)])
        assert result.exit_code == 0
        assert "Report written to" in result.output
        data = json.loads(out.read_text())
        assert data["overall_score"] == 85

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_score_text_to_file(
        self, mock_extract: MagicMock, mock_score: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """Text output --output writes to a file."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        out = tmp_path / "report.txt"
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--output", str(out)])
        assert result.exit_code == 0
        assert "Report written to" in result.output
        text = out.read_text()
        assert "ATS Compatibility Report" in text

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_score_verbose(
        self, mock_extract: MagicMock, mock_score: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """--verbose shows confidence levels."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--verbose"])
        assert result.exit_code == 0
        assert "opinionated heuristic" in result.output


class TestScoreWithJob:
    """Score command with --job flag."""

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    @patch("anvilcv.tailoring.job_parser.parse_job_from_file")
    def test_score_with_job(
        self,
        mock_parse_job: MagicMock,
        mock_extract: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """--job passes parsed job description to scorer."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Senior Python Developer at Acme Corp")

        mock_job = MagicMock()
        mock_parse_job.return_value = mock_job
        mock_extract.return_value = _make_doc()
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
        assert "Keywords:" in result.output
        assert "Matched: python" in result.output
        assert "Missing: django" in result.output

    @patch(_EXTRACT)
    @patch("anvilcv.tailoring.job_parser.parse_job_from_file")
    def test_score_job_parse_error(
        self, mock_parse_job: MagicMock, mock_extract: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """Bad --job file exits with code 1."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        job_file = tmp_path / "bad_job.txt"
        job_file.write_text("invalid")
        mock_extract.return_value = _make_doc()
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

    @patch(_EXTRACT)
    def test_score_extract_error(self, mock_extract: MagicMock, tmp_path: pathlib.Path) -> None:
        """AnvilUserError from extract_text exits with code 1."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_extract.side_effect = AnvilUserError(message="corrupt PDF")

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 1
        assert "Error: corrupt PDF" in result.output


class TestScorePdfExtraction:
    """Test PDF extraction failure and partial extraction handling."""

    @patch(_EXTRACT)
    def test_empty_pdf_exits_1(self, mock_extract: MagicMock, tmp_path: pathlib.Path) -> None:
        """Image-based PDF with no text exits 1 with helpful message."""
        pdf = tmp_path / "scanned.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_extract.return_value = _make_doc(
            full_text="",
            source_type="pdf",
            image_page_count=2,
            page_count=2,
        )

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 1
        assert "image-based" in result.output
        assert "anvil score output/resume.html" in result.output

    @patch(_EXTRACT)
    def test_empty_pdf_no_images_exits_1(
        self, mock_extract: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """PDF with no text and no images still exits 1."""
        pdf = tmp_path / "empty.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_extract.return_value = _make_doc(
            full_text="",
            source_type="pdf",
            image_page_count=0,
            page_count=1,
        )

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 1
        assert "Could not extract text" in result.output

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_partial_pdf_warns_and_continues(
        self, mock_extract: MagicMock, mock_score: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """PDF with some image pages warns but continues scoring."""
        pdf = tmp_path / "partial.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        mock_extract.return_value = _make_doc(
            full_text="John Doe\nExperience",
            source_type="pdf",
            page_count=3,
            image_page_count=1,
        )
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 0
        assert "incomplete" in result.output
        assert "2 pages extracted" in result.output
        assert "1 appear to be images" in result.output

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_html_empty_does_not_trigger_pdf_message(
        self, mock_extract: MagicMock, mock_score: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """Empty HTML does not trigger the PDF-specific error message."""
        html = tmp_path / "resume.html"
        html.write_text("<html></html>")
        mock_extract.return_value = _make_doc(
            full_text="",
            source_type="html",
        )
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(html)])
        # Should NOT exit 1 with PDF message — only PDFs get this treatment
        assert "image-based" not in result.output


class TestScoreYamlInput:
    """Test scoring YAML input (auto-renders then scores)."""

    @patch("anvilcv.cli.score_command.score_command._render_yaml_for_scoring")
    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_yaml_input_renders_first(
        self,
        mock_extract: MagicMock,
        mock_score: MagicMock,
        mock_render: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """YAML input triggers rendering before scoring."""
        resume = tmp_path / "resume.yaml"
        resume.write_text("cv:\n  name: Test\n")
        html_output = tmp_path / "output.html"
        html_output.write_text("<html>scored</html>")
        mock_render.return_value = html_output
        mock_extract.return_value = _make_doc(source_type="html")
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(resume)])
        assert result.exit_code == 0
        mock_render.assert_called_once_with(resume)
        assert "85/100" in result.output

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_pdf_input_no_render(
        self,
        mock_extract: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """PDF input does not trigger rendering."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf)])
        assert result.exit_code == 0


class TestScoreYamlFormat:
    """Test --format yaml output."""

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_yaml_format_output(
        self,
        mock_extract: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """--format yaml produces valid YAML output."""
        import yaml  # type: ignore[import-untyped]

        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(app, ["score", str(pdf), "--format", "yaml"])
        assert result.exit_code == 0
        data = yaml.safe_load(result.output)
        assert data["overall_score"] == 85

    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_yaml_format_to_file(
        self,
        mock_extract: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """--format yaml --output writes to file."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        out = tmp_path / "report.yaml"
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(
            app,
            ["score", str(pdf), "--format", "yaml", "--output", str(out)],
        )
        assert result.exit_code == 0
        assert out.exists()
        assert "Report written to" in result.output


class TestScoreJobUrl:
    """Test --job with URL handling."""

    @patch("anvilcv.cli.job_input.resolve_job_input")
    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_job_url_resolves(
        self,
        mock_extract: MagicMock,
        mock_score: MagicMock,
        mock_resolve_job: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """--job accepts URL through resolve_job_input."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        mock_resolve_job.return_value = MagicMock()
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(
            app,
            ["score", str(pdf), "--job", "https://example.com/job"],
        )
        assert result.exit_code == 0
        mock_resolve_job.assert_called_once_with("https://example.com/job")

    @patch("anvilcv.cli.job_input.resolve_job_input")
    @patch(_SCORE_DOC)
    @patch(_EXTRACT)
    def test_job_service_error_continues(
        self,
        mock_extract: MagicMock,
        mock_score: MagicMock,
        mock_resolve_job: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """Service errors warn and continue scoring without keywords."""
        from anvilcv.exceptions import AnvilServiceError

        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        mock_resolve_job.side_effect = AnvilServiceError(message="Could not fetch URL")
        mock_extract.return_value = _make_doc()
        mock_score.return_value = _make_report()

        result = runner.invoke(
            app,
            ["score", str(pdf), "--job", "https://unreachable.com/job"],
        )
        assert result.exit_code == 0
        assert "Warning" in result.output
        # Scored without job description
        mock_score.assert_called_once()


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
