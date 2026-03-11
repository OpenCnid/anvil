"""Tests for vendored rendercv command registration on the Anvil CLI.

Why:
    The vendored render, new, and create-theme commands must register on the
    Anvil Typer app. If the vendor import hook or auto-discovery breaks, these
    commands silently disappear from ``anvil --help``. These tests catch that.

Note:
    All tests in this module use @pytest.mark.xdist_group("typer_cli") to
    ensure they run on the same parallel worker. Typer's invoke() calls
    get_type_hints() which fails when parallel mock tests interfere.
"""

import pytest
from typer.testing import CliRunner

runner = CliRunner()

pytestmark = pytest.mark.xdist_group("typer_cli")


def _ensure_commands_registered():
    """Explicitly import vendored commands to ensure they're registered.

    Why: Module-level autodiscovery in vendor/rendercv/cli/app.py only runs
    once per process. If another test on the same xdist worker imported the
    Anvil app first (e.g., test_entry_point patches app with MagicMock),
    the cached module may have stale command registrations.
    """
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    import anvilcv.vendor.rendercv.cli.new_command.new_command  # noqa: F401
    import anvilcv.vendor.rendercv.cli.render_command.render_command  # noqa: F401


def test_render_command_registered():
    """Vendored render command is available after importing vendor app."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert "YAML input file" in result.output


def test_render_variant_flag_in_help():
    """The render command has --variant flag."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert "--variant" in result.output


def test_render_variant_empty_dir_exits_1(tmp_path):
    """--variant with empty directory exits with code 1."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    empty_dir = tmp_path / "variants"
    empty_dir.mkdir()

    result = runner.invoke(
        app,
        ["render", "dummy.yaml", "--variant", str(empty_dir)],
    )
    assert result.exit_code == 1
    assert "No YAML files found" in result.output


def test_render_override_flag_in_help():
    """The render command has --override flag."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert "--override" in result.output
    assert "KEY=VALUE" in result.output


def test_render_override_invalid_format():
    """--override without = sign exits with code 1."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(
        app,
        ["render", "dummy.yaml", "--override", "noequals"],
    )
    assert result.exit_code == 1
    assert "Invalid --override format" in result.output


def test_render_override_parses_key_value():
    """--override KEY=VALUE is parsed correctly into overrides dict."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    # With a non-existent file, it will fail on file-not-found, not on override parsing
    result = runner.invoke(
        app,
        ["render", "nonexistent.yaml", "--override", "design.theme=devforge"],
    )
    # Should NOT fail with "Invalid --override format"
    assert "Invalid --override format" not in result.output


def test_render_override_multiple_values():
    """Multiple --override flags are all accepted."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(
        app,
        [
            "render",
            "nonexistent.yaml",
            "--override",
            "design.theme=devforge",
            "--override",
            "cv.name=Jane Doe",
        ],
    )
    assert "Invalid --override format" not in result.output


def test_render_override_value_with_equals():
    """--override handles values containing = signs."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(
        app,
        ["render", "nonexistent.yaml", "--override", "cv.note=a=b=c"],
    )
    assert "Invalid --override format" not in result.output


def test_new_command_registered():
    """Vendored new command is available."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["new", "--help"])
    assert result.exit_code == 0
    assert "full name" in result.output.lower() or "FULL_NAME" in result.output


def test_create_theme_command_registered():
    """Vendored create-theme command is available."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["create-theme", "--help"])
    assert result.exit_code == 0


def test_new_command_has_rendercv_compat_flag():
    """The new command exposes --rendercv-compat flag."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["new", "--help"])
    assert result.exit_code == 0
    assert "--rendercv-compat" in result.output


def test_new_command_generates_file_with_anvil(tmp_path, monkeypatch):
    """anvil new generates YAML with commented anvil section."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new", "Test User"])
    assert result.exit_code == 0
    yaml_file = tmp_path / "Test_User_CV.yaml"
    assert yaml_file.exists()
    content = yaml_file.read_text(encoding="utf-8")
    assert "# Anvil configuration" in content


def test_new_command_rendercv_compat_excludes_anvil(tmp_path, monkeypatch):
    """anvil new --rendercv-compat generates YAML without anvil section."""
    _ensure_commands_registered()
    from anvilcv.cli.app import app

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new", "Test User", "--rendercv-compat"])
    assert result.exit_code == 0
    yaml_file = tmp_path / "Test_User_CV.yaml"
    assert yaml_file.exists()
    content = yaml_file.read_text(encoding="utf-8")
    assert "# Anvil configuration" not in content
    assert "Test User" in content
