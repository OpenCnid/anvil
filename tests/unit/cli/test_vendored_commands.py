"""Tests for vendored rendercv command registration on the Anvil CLI.

Why:
    The vendored render, new, and create-theme commands must register on the
    Anvil Typer app. If the vendor import hook or auto-discovery breaks, these
    commands silently disappear from ``anvil --help``. These tests catch that.
"""

from typer.testing import CliRunner

runner = CliRunner()


def test_render_command_registered():
    """Vendored render command is available after importing vendor app."""
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert "YAML input file" in result.output


def test_new_command_registered():
    """Vendored new command is available."""
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["new", "--help"])
    assert result.exit_code == 0
    assert "full name" in result.output.lower() or "FULL_NAME" in result.output


def test_create_theme_command_registered():
    """Vendored create-theme command is available."""
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["create-theme", "--help"])
    assert result.exit_code == 0
