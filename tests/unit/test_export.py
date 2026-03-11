"""Tests for the export command.

Why:
    The export command strips the anvil section from YAML for rendercv
    compatibility. We verify it preserves all other content and handles
    edge cases (no anvil section, empty files).
"""

import pathlib

from ruamel.yaml import YAML
from typer.testing import CliRunner

import anvilcv.cli.export_command  # noqa: F401
from anvilcv.cli.app import app

runner = CliRunner()


class TestExportCommand:
    def test_strips_anvil_section(self, sample_anvil_yaml: pathlib.Path, tmp_path: pathlib.Path):
        output = tmp_path / "exported.yaml"
        result = runner.invoke(
            app,
            [
                "export",
                str(sample_anvil_yaml),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0
        assert "Exported to" in result.output

        yaml = YAML()
        with open(output) as f:
            data = yaml.load(f)
        assert "anvil" not in data
        assert data["cv"]["name"] == "Jane Developer"

    def test_no_anvil_section(self, sample_rendercv_yaml: pathlib.Path):
        result = runner.invoke(
            app,
            [
                "export",
                str(sample_rendercv_yaml),
            ],
        )
        assert result.exit_code == 0
        assert "already rendercv-compatible" in result.output

    def test_default_output_name(self, sample_anvil_yaml: pathlib.Path):
        result = runner.invoke(
            app,
            [
                "export",
                str(sample_anvil_yaml),
            ],
        )
        assert result.exit_code == 0
        expected = sample_anvil_yaml.parent / f"{sample_anvil_yaml.stem}_rendercv.yaml"
        assert expected.exists()

    def test_preserves_cv_content(self, sample_anvil_yaml: pathlib.Path, tmp_path: pathlib.Path):
        output = tmp_path / "exported.yaml"
        runner.invoke(
            app,
            [
                "export",
                str(sample_anvil_yaml),
                "--output",
                str(output),
            ],
        )

        yaml = YAML()
        with open(sample_anvil_yaml) as f:
            original = yaml.load(f)
        with open(output) as f:
            exported = yaml.load(f)

        assert exported["cv"] == original["cv"]
