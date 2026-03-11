"""Tests for Anvil extensions to the vendored sample generator.

Why:
    X.3 extends sample_generator.py and sample_content.yaml to include
    Anvil-specific configuration (AI providers, GitHub, variants) in
    generated YAML. These tests verify:
    - The anvil section appears commented-out in generated output
    - The --rendercv-compat flag suppresses the anvil section
    - Generated YAML remains valid and parseable
    - Backward compatibility with pure rendercv YAML is preserved
"""

from __future__ import annotations

import pathlib

import ruamel.yaml

from anvilcv.vendor.rendercv.schema.sample_generator import (
    create_sample_yaml_input_file,
)


class TestAnvilSampleSection:
    """Tests for the anvil section in generated sample YAML."""

    def test_default_output_includes_anvil_comment(self) -> None:
        """Generated YAML includes a commented-out anvil section by default."""
        yaml_str = create_sample_yaml_input_file(file_path=None)
        assert yaml_str is not None
        assert "# Anvil configuration" in yaml_str
        assert "# anvil:" in yaml_str

    def test_anvil_section_has_provider_config(self) -> None:
        """The commented anvil section shows AI provider configuration."""
        yaml_str = create_sample_yaml_input_file(file_path=None)
        assert yaml_str is not None
        assert "anthropic" in yaml_str
        assert "openai" in yaml_str
        assert "ollama" in yaml_str

    def test_anvil_section_has_github_config(self) -> None:
        """The commented anvil section shows GitHub configuration."""
        yaml_str = create_sample_yaml_input_file(file_path=None)
        assert yaml_str is not None
        assert "github" in yaml_str
        assert "username" in yaml_str

    def test_anvil_section_has_variants_config(self) -> None:
        """The commented anvil section shows variant configuration."""
        yaml_str = create_sample_yaml_input_file(file_path=None)
        assert yaml_str is not None
        assert "variants" in yaml_str
        assert "output_dir" in yaml_str

    def test_anvil_section_is_commented_out(self) -> None:
        """The anvil section is entirely commented out (not active YAML)."""
        yaml_str = create_sample_yaml_input_file(file_path=None)
        assert yaml_str is not None
        # Parse the YAML — anvil should NOT appear as a key since it's commented
        yaml = ruamel.yaml.YAML()
        parsed = yaml.load(yaml_str)
        assert "anvil" not in parsed, "anvil section should be commented out, not active YAML"

    def test_rendercv_compat_excludes_anvil(self) -> None:
        """include_anvil=False produces pure rendercv YAML without anvil section."""
        yaml_str = create_sample_yaml_input_file(file_path=None, include_anvil=False)
        assert yaml_str is not None
        assert "# Anvil configuration" not in yaml_str
        assert "# anvil:" not in yaml_str

    def test_rendercv_compat_is_valid_yaml(self) -> None:
        """rendercv-compat output is valid, parseable YAML."""
        yaml_str = create_sample_yaml_input_file(file_path=None, include_anvil=False)
        assert yaml_str is not None
        yaml = ruamel.yaml.YAML()
        parsed = yaml.load(yaml_str)
        assert "cv" in parsed
        assert "design" in parsed

    def test_default_output_is_valid_yaml(self) -> None:
        """Default output (with commented anvil) is valid, parseable YAML."""
        yaml_str = create_sample_yaml_input_file(file_path=None)
        assert yaml_str is not None
        yaml = ruamel.yaml.YAML()
        parsed = yaml.load(yaml_str)
        assert "cv" in parsed
        assert "design" in parsed

    def test_file_write_with_anvil(self, tmp_path: pathlib.Path) -> None:
        """File output includes the anvil section."""
        out = tmp_path / "test_cv.yaml"
        create_sample_yaml_input_file(file_path=out, name="Test User")
        content = out.read_text(encoding="utf-8")
        assert "# Anvil configuration" in content
        assert "Test User" in content

    def test_file_write_rendercv_compat(self, tmp_path: pathlib.Path) -> None:
        """File output with rendercv-compat excludes the anvil section."""
        out = tmp_path / "test_cv.yaml"
        create_sample_yaml_input_file(file_path=out, name="Test User", include_anvil=False)
        content = out.read_text(encoding="utf-8")
        assert "# Anvil configuration" not in content
        assert "Test User" in content

    def test_devforge_theme_with_anvil(self) -> None:
        """devforge theme works with anvil section included."""
        yaml_str = create_sample_yaml_input_file(file_path=None, theme="devforge")
        assert yaml_str is not None
        assert "devforge" in yaml_str
        assert "# Anvil configuration" in yaml_str

    def test_all_themes_work_with_anvil(self) -> None:
        """All available themes produce valid output with anvil section."""
        from anvilcv.vendor.rendercv.schema.models.design.built_in_design import (
            available_themes,
        )

        for theme in available_themes:
            yaml_str = create_sample_yaml_input_file(file_path=None, theme=theme)
            assert yaml_str is not None, f"Failed for theme: {theme}"
            assert "# Anvil configuration" in yaml_str, f"Missing anvil section for theme: {theme}"


class TestSampleContentYaml:
    """Tests for the extended sample_content.yaml file."""

    def test_sample_content_has_anvil_section(self) -> None:
        """sample_content.yaml contains the anvil section."""
        sample_path = (
            pathlib.Path(__file__).resolve().parents[3]
            / "src"
            / "anvilcv"
            / "vendor"
            / "rendercv"
            / "schema"
            / "sample_content.yaml"
        )
        yaml = ruamel.yaml.YAML()
        with open(sample_path, encoding="utf-8") as f:
            data = yaml.load(f)
        assert "anvil" in data
        assert "providers" in data["anvil"]
        assert "github" in data["anvil"]
        assert "variants" in data["anvil"]

    def test_sample_content_provider_defaults(self) -> None:
        """Sample anvil config has sensible provider defaults."""
        sample_path = (
            pathlib.Path(__file__).resolve().parents[3]
            / "src"
            / "anvilcv"
            / "vendor"
            / "rendercv"
            / "schema"
            / "sample_content.yaml"
        )
        yaml = ruamel.yaml.YAML()
        with open(sample_path, encoding="utf-8") as f:
            data = yaml.load(f)
        providers = data["anvil"]["providers"]
        assert providers["default"] == "anthropic"
        assert "anthropic" in providers
        assert "openai" in providers
        assert "ollama" in providers

    def test_sample_content_cv_section_unchanged(self) -> None:
        """The cv section in sample_content.yaml still has expected content."""
        sample_path = (
            pathlib.Path(__file__).resolve().parents[3]
            / "src"
            / "anvilcv"
            / "vendor"
            / "rendercv"
            / "schema"
            / "sample_content.yaml"
        )
        yaml = ruamel.yaml.YAML()
        with open(sample_path, encoding="utf-8") as f:
            data = yaml.load(f)
        assert "cv" in data
        assert data["cv"]["name"] == "John Doe"
        assert "sections" in data["cv"]
