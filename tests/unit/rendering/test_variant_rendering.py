"""Tests for multi-variant rendering.

Why:
    Variant rendering discovers YAML files in a directory and renders each
    one into its own output subfolder. Tests verify discovery, path resolution,
    metadata reading, and error handling without invoking the full render pipeline.
"""

import pathlib
from unittest.mock import MagicMock, patch

from anvilcv.rendering.variant_renderer import (
    discover_variants,
    get_variant_output_folder,
    read_variant_metadata,
    render_all_variants,
    render_variant,
)

SAMPLE_VARIANT_YAML = """\
cv:
  name: Jane Developer
  sections:
    experience:
      - company: Acme Corp
        position: Engineer
        start_date: 2020-01
        end_date: present
        highlights:
          - Built scalable APIs using Python and FastAPI
variant:
  source: Jane_Developer_CV.yaml
  job: jobs/acme.yaml
  created_at: "2026-03-11T10:00:00"
  provider: anthropic
  model: claude-sonnet-4-20250514
  changes:
    - section: experience.0.highlights.0
      action: rewritten
      detail: Tailored for job match
"""

SAMPLE_PLAIN_YAML = """\
cv:
  name: John Doe
  sections:
    skills:
      - label: Languages
        details: Python, Go
"""


class TestDiscoverVariants:
    def test_finds_yaml_files(self, tmp_path: pathlib.Path):
        (tmp_path / "a.yaml").write_text(SAMPLE_VARIANT_YAML)
        (tmp_path / "b.yml").write_text(SAMPLE_PLAIN_YAML)
        (tmp_path / "c.txt").write_text("not yaml")

        variants = discover_variants(tmp_path)
        assert len(variants) == 2
        names = [v.name for v in variants]
        assert "a.yaml" in names
        assert "b.yml" in names

    def test_returns_sorted(self, tmp_path: pathlib.Path):
        (tmp_path / "z_variant.yaml").write_text(SAMPLE_PLAIN_YAML)
        (tmp_path / "a_variant.yaml").write_text(SAMPLE_PLAIN_YAML)
        (tmp_path / "m_variant.yaml").write_text(SAMPLE_PLAIN_YAML)

        variants = discover_variants(tmp_path)
        names = [v.name for v in variants]
        assert names == ["a_variant.yaml", "m_variant.yaml", "z_variant.yaml"]

    def test_empty_directory(self, tmp_path: pathlib.Path):
        variants = discover_variants(tmp_path)
        assert variants == []

    def test_nonexistent_directory(self, tmp_path: pathlib.Path):
        variants = discover_variants(tmp_path / "nonexistent")
        assert variants == []

    def test_ignores_non_yaml_files(self, tmp_path: pathlib.Path):
        (tmp_path / "readme.md").write_text("# Variants")
        (tmp_path / "config.json").write_text("{}")
        (tmp_path / "real.yaml").write_text(SAMPLE_PLAIN_YAML)

        variants = discover_variants(tmp_path)
        assert len(variants) == 1
        assert variants[0].name == "real.yaml"


class TestGetVariantOutputFolder:
    def test_default_output_folder(self, tmp_path: pathlib.Path):
        variant = tmp_path / "variants" / "Jane_Acme_2026.yaml"
        result = get_variant_output_folder(variant)
        assert result == tmp_path / "variants" / "rendercv_output" / "Jane_Acme_2026"

    def test_custom_base_output(self, tmp_path: pathlib.Path):
        variant = tmp_path / "Jane_Acme.yaml"
        base = tmp_path / "output"
        result = get_variant_output_folder(variant, base_output=base)
        assert result == tmp_path / "output" / "Jane_Acme"

    def test_preserves_variant_stem(self, tmp_path: pathlib.Path):
        variant = tmp_path / "My_Resume_Google_2026-03-11.yaml"
        result = get_variant_output_folder(variant)
        assert result.name == "My_Resume_Google_2026-03-11"


class TestReadVariantMetadata:
    def test_reads_variant_section(self, tmp_path: pathlib.Path):
        variant_file = tmp_path / "variant.yaml"
        variant_file.write_text(SAMPLE_VARIANT_YAML)

        metadata = read_variant_metadata(variant_file)
        assert metadata is not None
        assert metadata["source"] == "Jane_Developer_CV.yaml"
        assert metadata["provider"] == "anthropic"
        assert len(metadata["changes"]) == 1

    def test_returns_none_for_plain_yaml(self, tmp_path: pathlib.Path):
        plain_file = tmp_path / "plain.yaml"
        plain_file.write_text(SAMPLE_PLAIN_YAML)

        metadata = read_variant_metadata(plain_file)
        assert metadata is None

    def test_returns_none_for_invalid_yaml(self, tmp_path: pathlib.Path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{{invalid yaml")

        metadata = read_variant_metadata(bad_file)
        assert metadata is None

    def test_returns_none_for_missing_file(self, tmp_path: pathlib.Path):
        metadata = read_variant_metadata(tmp_path / "missing.yaml")
        assert metadata is None

    def test_returns_none_for_non_dict_yaml(self, tmp_path: pathlib.Path):
        """Cover line 68: YAML that parses to non-dict returns None."""
        scalar_file = tmp_path / "scalar.yaml"
        scalar_file.write_text("just a string")
        metadata = read_variant_metadata(scalar_file)
        assert metadata is None

    def test_returns_none_for_empty_yaml(self, tmp_path: pathlib.Path):
        """Cover line 68: empty YAML (None data) returns None."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        metadata = read_variant_metadata(empty_file)
        assert metadata is None


# --- render_variant tests (mocked) ---


class TestRenderVariant:
    @patch("anvilcv.vendor.rendercv.cli.render_command.run_rendercv.run_rendercv")
    @patch("anvilcv.vendor.rendercv.cli.render_command.progress_panel.ProgressPanel")
    def test_render_variant_default_output(self, mock_panel_cls, mock_run, tmp_path: pathlib.Path):
        """Cover lines 89-104: render_variant with default output folder."""
        mock_panel = MagicMock()
        mock_panel_cls.return_value.__enter__ = lambda self: mock_panel
        mock_panel_cls.return_value.__exit__ = lambda self, *a: None

        variant = tmp_path / "variants" / "Jane_Acme.yaml"
        variant.parent.mkdir(parents=True, exist_ok=True)
        variant.write_text(SAMPLE_VARIANT_YAML)

        result = render_variant(variant)
        expected_out = tmp_path / "variants" / "rendercv_output" / "Jane_Acme"
        assert result == expected_out
        mock_run.assert_called_once()

    @patch("anvilcv.vendor.rendercv.cli.render_command.run_rendercv.run_rendercv")
    @patch("anvilcv.vendor.rendercv.cli.render_command.progress_panel.ProgressPanel")
    def test_render_variant_custom_output(self, mock_panel_cls, mock_run, tmp_path: pathlib.Path):
        """Cover lines 89-104: render_variant with custom output folder."""
        mock_panel = MagicMock()
        mock_panel_cls.return_value.__enter__ = lambda self: mock_panel
        mock_panel_cls.return_value.__exit__ = lambda self, *a: None

        variant = tmp_path / "Jane_Acme.yaml"
        variant.write_text(SAMPLE_VARIANT_YAML)
        custom_out = tmp_path / "my_output"

        result = render_variant(variant, output_folder=custom_out)
        assert result == custom_out


# --- render_all_variants tests (mocked) ---


class TestRenderAllVariants:
    @patch("anvilcv.rendering.variant_renderer.render_variant")
    def test_render_all_success(self, mock_render, tmp_path: pathlib.Path):
        """Cover lines 122-134: render all variants in a directory."""
        (tmp_path / "a.yaml").write_text(SAMPLE_VARIANT_YAML)
        (tmp_path / "b.yaml").write_text(SAMPLE_PLAIN_YAML)

        mock_render.return_value = tmp_path / "output"

        results = render_all_variants(tmp_path)
        assert len(results) == 2
        assert mock_render.call_count == 2

    @patch("anvilcv.rendering.variant_renderer.render_variant")
    def test_render_all_with_base_output(self, mock_render, tmp_path: pathlib.Path):
        """Cover lines 122-134: base_output is used for output folders."""
        (tmp_path / "a.yaml").write_text(SAMPLE_VARIANT_YAML)

        mock_render.return_value = tmp_path / "out" / "a"
        base = tmp_path / "out"

        results = render_all_variants(tmp_path, base_output=base)
        assert len(results) == 1
        # Verify the output folder passed is base_output / stem
        call_kwargs = mock_render.call_args
        assert call_kwargs[1]["output_folder"] == base / "a"

    @patch("anvilcv.rendering.variant_renderer.render_variant")
    def test_render_all_partial_failure(self, mock_render, tmp_path: pathlib.Path):
        """Cover line 130-132: individual failures don't stop the batch."""
        (tmp_path / "a.yaml").write_text(SAMPLE_VARIANT_YAML)
        (tmp_path / "b.yaml").write_text(SAMPLE_PLAIN_YAML)

        # First succeeds, second fails
        def side_effect(path, output_folder, **kwargs):
            if path.stem == "a":
                return output_folder
            raise RuntimeError("Render failed")

        mock_render.side_effect = side_effect

        results = render_all_variants(tmp_path)
        assert len(results) == 1
        assert results[0][0].stem == "a"

    @patch("anvilcv.rendering.variant_renderer.render_variant")
    def test_render_all_empty_dir(self, mock_render, tmp_path: pathlib.Path):
        """Cover line 122: empty directory yields empty results."""
        results = render_all_variants(tmp_path)
        assert results == []
        mock_render.assert_not_called()
