"""Tests for CLI scaffold: --help, --version, subcommand registration.

Why:
    The CLI is the user-facing surface. If ``anvil --help`` doesn't list all
    commands or ``anvil --version`` shows the wrong version, users lose trust.
    These tests verify the Typer app is wired correctly before any feature
    implementation.
"""

from typer.testing import CliRunner

import anvilcv.cli.score_command.score_command  # noqa: F401  # register score command
from anvilcv.cli.app import app

runner = CliRunner()


class TestCLIVersion:
    def test_version_flag(self):
        """``anvil --version`` prints AnvilCV version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "AnvilCV v0.1.0" in result.output

    def test_version_short_flag(self):
        """``anvil -v`` also prints version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "AnvilCV v0.1.0" in result.output


class TestCLIHelp:
    def test_help_flag(self):
        """``anvil --help`` shows help text."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AnvilCV" in result.output

    def test_no_args_shows_help(self):
        """Running ``anvil`` with no args shows help."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0


class TestStubCommands:
    """Stub commands print 'not yet implemented' and exit 0."""

    def test_score_requires_input(self):
        result = runner.invoke(app, ["score"])
        assert result.exit_code == 2  # Missing required argument

    def test_tailor_stub(self):
        result = runner.invoke(app, ["tailor"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output

    def test_scan_stub(self):
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output

    def test_prep_stub(self):
        result = runner.invoke(app, ["prep"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output

    def test_cover_stub(self):
        result = runner.invoke(app, ["cover"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output

    def test_watch_stub(self):
        result = runner.invoke(app, ["watch"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output

    def test_deploy_stub(self):
        result = runner.invoke(app, ["deploy"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output

    def test_export_stub(self):
        result = runner.invoke(app, ["export"])
        assert result.exit_code == 0
        assert "not yet implemented" in result.output


class TestStubCommandHelp:
    """Each stub command has --help."""

    def test_score_help(self):
        result = runner.invoke(app, ["score", "--help"])
        assert result.exit_code == 0
        assert "ATS" in result.output or "score" in result.output.lower()

    def test_tailor_help(self):
        result = runner.invoke(app, ["tailor", "--help"])
        assert result.exit_code == 0

    def test_export_help(self):
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
