"""Tests for devforge theme — model validation, Typst generation, Markdown generation.

Why:
    The devforge theme is a standalone theme with its own Pydantic model and
    Typst templates. Tests verify: model validation, theme registration in the
    discriminated union, Typst source generation for all entry types, and
    Markdown generation (using shared templates).
"""

from __future__ import annotations

import pathlib

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CORPUS_DIR = pathlib.Path(__file__).resolve().parents[1] / "corpus"


@pytest.fixture
def devforge_yaml(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal devforge-themed YAML file."""
    yaml_content = """\
cv:
  name: Test Developer
  location: Austin, TX
  email: test@example.com
  sections:
    experience:
      - company: TechCorp
        position: Senior Engineer
        start_date: 2021-01
        end_date: present
        location: Austin, TX
        highlights:
          - Built scalable data pipeline
    education:
      - institution: MIT
        area: Computer Science
        degree: BS
        start_date: 2017-09
        end_date: 2021-05
    projects:
      - name: myproject
        date: "2024"
        highlights:
          - Open source CLI tool
    skills:
      - label: Languages
        details: Python, Go, Rust
design:
  theme: devforge
"""
    yaml_file = tmp_path / "Test_Developer_CV.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file


@pytest.fixture
def devforge_corpus_yaml() -> pathlib.Path:
    """Return path to the devforge corpus YAML file."""
    return CORPUS_DIR / "devforge_engineer.yaml"


def _build_model(yaml_path: pathlib.Path):
    """Build a RenderCVModel from a YAML file."""
    from anvilcv.vendor.rendercv.schema.rendercv_model_builder import (
        build_rendercv_dictionary_and_model,
    )

    yaml_text = yaml_path.read_text(encoding="utf-8")
    _, model = build_rendercv_dictionary_and_model(yaml_text, input_file_path=yaml_path)
    return model


# ---------------------------------------------------------------------------
# Tests: Model validation
# ---------------------------------------------------------------------------


class TestDevforgeModel:
    """Test DevforgeTheme Pydantic model validation."""

    def test_model_validates(self, devforge_yaml: pathlib.Path):
        model = _build_model(devforge_yaml)
        assert model.design.theme == "devforge"

    def test_default_colors(self, devforge_yaml: pathlib.Path):
        model = _build_model(devforge_yaml)
        assert model.design.colors is not None
        assert model.design.colors.accent is not None

    def test_default_typography(self, devforge_yaml: pathlib.Path):
        model = _build_model(devforge_yaml)
        assert model.design.typography.font_family.body == "IBM Plex Sans"
        assert model.design.typography.font_family.mono == "IBM Plex Mono"

    def test_default_page(self, devforge_yaml: pathlib.Path):
        model = _build_model(devforge_yaml)
        assert model.design.page.size == "us-letter"
        assert model.design.page.top_margin == "0.6in"

    def test_skill_chips_enabled_by_default(self, devforge_yaml: pathlib.Path):
        model = _build_model(devforge_yaml)
        assert model.design.skill_chips.enabled is True

    def test_templates_present(self, devforge_yaml: pathlib.Path):
        model = _build_model(devforge_yaml)
        assert model.design.templates is not None
        assert model.design.templates.experience_entry is not None
        assert model.design.templates.education_entry is not None

    def test_custom_colors(self, tmp_path: pathlib.Path):
        yaml_content = """\
cv:
  name: Test
  sections:
    skills:
      - label: Languages
        details: Python
design:
  theme: devforge
  colors:
    accent: "rgb(255, 0, 0)"
"""
        yaml_file = tmp_path / "Test_CV.yaml"
        yaml_file.write_text(yaml_content)
        model = _build_model(yaml_file)
        assert "255" in str(model.design.colors.accent)


# ---------------------------------------------------------------------------
# Tests: Theme registration
# ---------------------------------------------------------------------------


class TestThemeRegistration:
    """Test devforge is registered as a built-in theme."""

    def test_devforge_in_available_themes(self):
        from anvilcv.vendor.rendercv.schema.models.design.built_in_design import (
            available_themes,
        )

        assert "devforge" in available_themes

    def test_devforge_theme_count(self):
        """All 6 themes should be registered: classic + 4 YAML variants + devforge."""
        from anvilcv.vendor.rendercv.schema.models.design.built_in_design import (
            available_themes,
        )

        assert len(available_themes) == 6


# ---------------------------------------------------------------------------
# Tests: Typst generation
# ---------------------------------------------------------------------------


class TestTypstGeneration:
    """Test that devforge generates valid Typst source."""

    def test_generates_typst(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        typst = render_full_template(model, "typst")
        assert typst is not None
        assert len(typst) > 0

    def test_typst_contains_import(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        typst = render_full_template(model, "typst")
        assert '#import "@preview/rendercv:0.2.0"' in typst

    def test_typst_contains_name(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        typst = render_full_template(model, "typst")
        assert "Test Developer" in typst

    def test_typst_contains_devforge_functions(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        typst = render_full_template(model, "typst")
        assert "devforge-entry" in typst
        assert "skill-chip" in typst

    def test_typst_contains_section_titles(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        typst = render_full_template(model, "typst")
        assert "Experience" in typst
        assert "Education" in typst
        assert "Projects" in typst
        assert "Skills" in typst

    def test_typst_contains_entry_content(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        typst = render_full_template(model, "typst")
        assert "TechCorp" in typst
        assert "Senior Engineer" in typst
        assert "MIT" in typst

    def test_corpus_generates_typst(self, devforge_corpus_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_corpus_yaml)
        typst = render_full_template(model, "typst")
        assert "Alex Rivera" in typst
        assert "Stripe" in typst


# ---------------------------------------------------------------------------
# Tests: Markdown generation (uses shared templates)
# ---------------------------------------------------------------------------


class TestMarkdownGeneration:
    """Test that devforge generates valid Markdown."""

    def test_generates_markdown(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        assert md is not None
        assert "Test Developer" in md

    def test_markdown_contains_sections(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        assert "Experience" in md
        assert "Education" in md
        assert "Skills" in md

    def test_markdown_contains_entries(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        assert "TechCorp" in md
        assert "MIT" in md

    def test_markdown_uses_devforge_header(self, devforge_yaml: pathlib.Path):
        """Devforge Header.j2.md uses '# Name's CV' format."""
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        assert "# Test Developer's CV" in md

    def test_markdown_uses_devforge_section_headings(self, devforge_yaml: pathlib.Path):
        """Devforge SectionBeginning.j2.md uses '# title' (h1) not '## title'."""
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        # Section titles should be h1 in devforge
        assert "\n# Experience" in md or md.startswith("# Experience")


# ---------------------------------------------------------------------------
# Tests: HTML generation (Full.html template)
# ---------------------------------------------------------------------------


class TestHtmlGeneration:
    """Test that devforge HTML uses the devforge Full.html template."""

    def test_generates_html(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
            render_html,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        html = render_html(model, md)
        assert html is not None
        assert "<!DOCTYPE html>" in html

    def test_html_uses_devforge_css_vars(self, devforge_yaml: pathlib.Path):
        """Devforge Full.html uses CSS custom properties like --accent-primary."""
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
            render_html,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        html = render_html(model, md)
        assert "--accent-primary" in html
        assert "--chip-bg" in html

    def test_html_contains_name(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
            render_html,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        html = render_html(model, md)
        assert "Test Developer" in html

    def test_html_has_print_styles(self, devforge_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_full_template,
            render_html,
        )

        model = _build_model(devforge_yaml)
        md = render_full_template(model, "markdown")
        html = render_html(model, md)
        assert "@media print" in html
