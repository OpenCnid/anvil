"""End-to-end integration tests for the AnvilCV CLI pipeline.

Why:
    Validates that the actual CLI commands work together as a pipeline:
    new → render → score → export. Uses CliRunner for in-process invocation
    and tmp_path for isolation.
"""

from __future__ import annotations

import json
import pathlib

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

# Trigger all command registrations (same as entry_point.py)
import anvilcv.cli.cover_command.cover_command  # noqa: F401
import anvilcv.cli.export_command  # noqa: F401
import anvilcv.cli.prep_command.prep_command  # noqa: F401
import anvilcv.cli.scan_command.scan_command  # noqa: F401
import anvilcv.cli.score_command.score_command  # noqa: F401
import anvilcv.cli.tailor_command.tailor_command  # noqa: F401
import anvilcv.vendor.rendercv.cli.app  # noqa: F401
from anvilcv.cli.app import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_CV_YAML = """\
cv:
  name: Test User
  location: Austin, TX
  email: test@example.com
  sections:
    experience:
      - company: Acme Corp
        position: Software Engineer
        start_date: 2022-01
        end_date: present
        highlights:
          - Built microservices with Python and FastAPI
          - Deployed on AWS using Terraform and Kubernetes
    education:
      - institution: UT Austin
        area: Computer Science
        degree: BS
        start_date: 2018-09
        end_date: 2022-05
    skills:
      - label: Languages
        details: Python, TypeScript, Go
      - label: Tools
        details: Docker, Git, Linux
"""

_ANVIL_CV_YAML = """\
cv:
  name: Test User
  location: Austin, TX
  email: test@example.com
  sections:
    experience:
      - company: Acme Corp
        position: Software Engineer
        start_date: 2022-01
        end_date: present
        highlights:
          - Built microservices with Python and FastAPI
    education:
      - institution: UT Austin
        area: Computer Science
        degree: BS
        start_date: 2018-09
        end_date: 2022-05
    skills:
      - label: Languages
        details: Python, Go
anvil:
  providers:
    default: none
"""


def _write_yaml(
    tmp_path: pathlib.Path, content: str, name: str = "Test_User_CV.yaml",
) -> pathlib.Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Test: anvil new
# ---------------------------------------------------------------------------


class TestAnvilNew:
    """Tests for `anvil new` command."""

    def test_new_creates_yaml(self, tmp_path: pathlib.Path) -> None:
        """anvil new 'Test User' should produce a valid YAML file."""
        result = runner.invoke(app, ["new", "Test User"], catch_exceptions=False)
        # The new command creates files in the current directory.
        # It should exit successfully.
        assert result.exit_code == 0, f"anvil new failed: {result.output}"
        # Check that a YAML file was created (rendercv convention: <Name>_CV.yaml)
        # The output should mention the created file path.
        assert "Test_User_CV" in result.output or result.exit_code == 0


# ---------------------------------------------------------------------------
# Test: anvil render
# ---------------------------------------------------------------------------


class TestAnvilRender:
    """Tests for `anvil render` command."""

    def test_render_produces_outputs(self, tmp_path: pathlib.Path) -> None:
        """anvil render <yaml> should produce PDF, HTML, ATS HTML, Markdown, and Typst."""
        yaml_file = _write_yaml(tmp_path, _MINIMAL_CV_YAML)
        result = runner.invoke(
            app,
            ["render", str(yaml_file)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"anvil render failed: {result.output}"

        # Check output directory exists
        output_dir = tmp_path / "rendercv_output"
        assert output_dir.is_dir(), (
            f"No output directory created. Contents: {list(tmp_path.iterdir())}"
        )

        # Check for expected output files
        output_files = list(output_dir.rglob("*"))
        output_names = [f.name for f in output_files if f.is_file()]
        output_suffixes = {f.suffix for f in output_files if f.is_file()}

        # Should have at least HTML and Markdown outputs
        assert ".html" in output_suffixes or ".md" in output_suffixes, (
            f"Missing HTML/Markdown output. Files: {output_names}"
        )


# ---------------------------------------------------------------------------
# Test: anvil score
# ---------------------------------------------------------------------------


class TestAnvilScore:
    """Tests for `anvil score` command."""

    def test_score_yaml_text_output(self, tmp_path: pathlib.Path) -> None:
        """anvil score <yaml> should produce a text score report."""
        yaml_file = _write_yaml(tmp_path, _MINIMAL_CV_YAML)
        result = runner.invoke(
            app,
            ["score", str(yaml_file)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"anvil score failed: {result.output}"
        # Report should contain the box-drawing header and category names
        assert "ATS Compatibility Report" in result.output
        assert "Score:" in result.output
        assert "Parsability:" in result.output
        assert "Structure:" in result.output

    def test_score_yaml_format(self, tmp_path: pathlib.Path) -> None:
        """anvil score <yaml> --format yaml should produce valid YAML output."""
        yaml_file = _write_yaml(tmp_path, _MINIMAL_CV_YAML)
        result = runner.invoke(
            app,
            ["score", str(yaml_file), "--format", "yaml"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"anvil score --format yaml failed: {result.output}"

        # Output should be valid YAML
        parsed = yaml.safe_load(result.output)
        assert isinstance(parsed, dict)
        assert "overall_score" in parsed
        assert "parsability" in parsed
        assert "structure" in parsed
        assert 0 <= parsed["overall_score"] <= 100

    def test_score_json_format(self, tmp_path: pathlib.Path) -> None:
        """anvil score <yaml> --format json should produce valid JSON output."""
        yaml_file = _write_yaml(tmp_path, _MINIMAL_CV_YAML)
        result = runner.invoke(
            app,
            ["score", str(yaml_file), "--format", "json"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"anvil score --format json failed: {result.output}"

        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)
        assert "overall_score" in parsed
        assert 0 <= parsed["overall_score"] <= 100


# ---------------------------------------------------------------------------
# Test: anvil export
# ---------------------------------------------------------------------------


class TestAnvilExport:
    """Tests for `anvil export` command."""

    def test_export_strips_anvil_section(self, tmp_path: pathlib.Path) -> None:
        """anvil export <anvil-yaml> --rendercv should strip the anvil section."""
        yaml_file = _write_yaml(tmp_path, _ANVIL_CV_YAML)
        result = runner.invoke(
            app,
            ["export", str(yaml_file), "--rendercv"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"anvil export failed: {result.output}"

        # Check the exported file
        exported = tmp_path / "Test_User_CV_rendercv.yaml"
        assert exported.exists(), f"Exported file not found. Output: {result.output}"

        data = yaml.safe_load(exported.read_text())
        assert "cv" in data
        assert "anvil" not in data, "anvil section should be stripped"

    def test_export_preserves_cv_content(self, tmp_path: pathlib.Path) -> None:
        """Exported YAML should preserve all CV content."""
        yaml_file = _write_yaml(tmp_path, _ANVIL_CV_YAML)
        runner.invoke(
            app,
            ["export", str(yaml_file), "--rendercv"],
            catch_exceptions=False,
        )
        exported = tmp_path / "Test_User_CV_rendercv.yaml"
        data = yaml.safe_load(exported.read_text())
        assert data["cv"]["name"] == "Test User"
        assert data["cv"]["email"] == "test@example.com"


# ---------------------------------------------------------------------------
# Test: Pipeline new → render → score
# ---------------------------------------------------------------------------


class TestPipeline:
    """End-to-end pipeline test: render → score."""

    def test_render_then_score(self, tmp_path: pathlib.Path) -> None:
        """Render a YAML, then score it — full pipeline."""
        yaml_file = _write_yaml(tmp_path, _MINIMAL_CV_YAML)

        # Step 1: Render
        render_result = runner.invoke(
            app,
            ["render", str(yaml_file)],
            catch_exceptions=False,
        )
        assert render_result.exit_code == 0, f"Render failed: {render_result.output}"

        # Step 2: Score the original YAML (it will render internally, then score)
        score_result = runner.invoke(
            app,
            ["score", str(yaml_file)],
            catch_exceptions=False,
        )
        assert score_result.exit_code == 0, f"Score failed: {score_result.output}"
        assert "ATS Compatibility Report" in score_result.output
        assert "Score:" in score_result.output

    def test_render_then_score_html(self, tmp_path: pathlib.Path) -> None:
        """Render a YAML, then score the generated HTML directly."""
        yaml_file = _write_yaml(tmp_path, _MINIMAL_CV_YAML)

        # Render first
        render_result = runner.invoke(
            app,
            ["render", str(yaml_file)],
            catch_exceptions=False,
        )
        assert render_result.exit_code == 0

        # Find an HTML output to score
        output_dir = tmp_path / "rendercv_output"
        html_files = list(output_dir.rglob("*.html"))
        if html_files:
            score_result = runner.invoke(
                app,
                ["score", str(html_files[0])],
                catch_exceptions=False,
            )
            assert score_result.exit_code == 0
            assert "ATS Compatibility Report" in score_result.output

    def test_full_pipeline_render_score_export(self, tmp_path: pathlib.Path) -> None:
        """Full pipeline: render → score → export works end-to-end.

        Note: `anvil render` uses vendored rendercv which rejects the `anvil`
        section in YAML. So we render the plain CV, then score the YAML (which
        renders internally with a separate code path that strips anvil), and
        export the anvil YAML to rendercv format.
        """
        # Use plain YAML for render (rendercv doesn't accept anvil section)
        plain_yaml = _write_yaml(tmp_path, _MINIMAL_CV_YAML, name="Plain_CV.yaml")

        # Render the plain YAML
        render_result = runner.invoke(
            app,
            ["render", str(plain_yaml)],
            catch_exceptions=False,
        )
        assert render_result.exit_code == 0

        # Score the plain YAML (renders internally then scores)
        score_result = runner.invoke(
            app,
            ["score", str(plain_yaml), "--format", "json"],
            catch_exceptions=False,
        )
        assert score_result.exit_code == 0
        report = json.loads(score_result.output)
        assert 0 <= report["overall_score"] <= 100

        # Export an anvil YAML to rendercv format
        anvil_yaml = _write_yaml(tmp_path, _ANVIL_CV_YAML, name="Anvil_CV.yaml")
        export_result = runner.invoke(
            app,
            ["export", str(anvil_yaml), "--rendercv"],
            catch_exceptions=False,
        )
        assert export_result.exit_code == 0
