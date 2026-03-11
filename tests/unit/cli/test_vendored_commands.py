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


def test_render_variant_flag_in_help():
    """The render command has --variant flag."""
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert "--variant" in result.output


def test_render_variant_empty_dir_exits_1(tmp_path):
    """--variant with empty directory exits with code 1."""
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    from anvilcv.cli.app import app

    empty_dir = tmp_path / "variants"
    empty_dir.mkdir()

    result = runner.invoke(
        app,
        ["render", "dummy.yaml", "--variant", str(empty_dir)],
    )
    assert result.exit_code == 1
    assert "No YAML files found" in result.output


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


def test_new_command_has_rendercv_compat_flag():
    """The new command exposes --rendercv-compat flag."""
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    from anvilcv.cli.app import app

    result = runner.invoke(app, ["new", "--help"])
    assert result.exit_code == 0
    assert "--rendercv-compat" in result.output


def test_new_command_generates_file_with_anvil(tmp_path, monkeypatch):
    """anvil new generates YAML with commented anvil section."""
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
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
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401
    from anvilcv.cli.app import app

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new", "Test User", "--rendercv-compat"])
    assert result.exit_code == 0
    yaml_file = tmp_path / "Test_User_CV.yaml"
    assert yaml_file.exists()
    content = yaml_file.read_text(encoding="utf-8")
    assert "# Anvil configuration" not in content
    assert "Test User" in content
