"""Tests for multi-variant rendering.

Why:
    Variant rendering discovers YAML files in a directory and renders each
    one into its own output subfolder. Tests verify discovery, path resolution,
    metadata reading, and error handling without invoking the full render pipeline.
"""

import pathlib

from anvilcv.rendering.variant_renderer import (
    discover_variants,
    get_variant_output_folder,
    read_variant_metadata,
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
