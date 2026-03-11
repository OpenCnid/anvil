"""Tests for ATS HTML pipeline integration.

Why:
    The ATS HTML renderer must integrate with the vendored render pipeline:
    templater bridge (model → dict), file generation (html.py), CLI flag
    (--no-ats-html), and the run_rendercv pipeline step. These tests verify
    each integration point works correctly.
"""

from __future__ import annotations

import pathlib

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_cv_yaml(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal valid rendercv YAML file with social networks."""
    yaml_content = """\
cv:
  name: Alice Tester
  location: Boston, MA
  email: alice@example.com
  phone: "+49 151 12345678"
  website: https://alice.dev
  social_networks:
    - network: LinkedIn
      username: alice-tester
    - network: GitHub
      username: alicetest
  sections:
    experience:
      - company: BigCorp
        position: Staff Engineer
        start_date: 2020-01
        end_date: present
        location: Boston, MA
        highlights:
          - Led platform team of 8 engineers
          - Reduced deployment time by 70%
    education:
      - institution: MIT
        area: Computer Science
        degree: BS
        start_date: 2016-09
        end_date: 2020-05
    skills:
      - label: Languages
        details: Python, Go, Rust
design:
  theme: classic
"""
    yaml_file = tmp_path / "Alice_Tester_CV.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file


def _build_model(yaml_path: pathlib.Path):
    """Build a RenderCVModel from a YAML file."""
    from anvilcv.vendor.rendercv.schema.rendercv_model_builder import (
        build_rendercv_dictionary_and_model,
    )

    yaml_text = yaml_path.read_text(encoding="utf-8")
    _, model = build_rendercv_dictionary_and_model(yaml_text, input_file_path=yaml_path)
    return model


# ---------------------------------------------------------------------------
# Tests: templater bridge — render_ats_html
# ---------------------------------------------------------------------------


class TestTemplaterBridge:
    """Test the render_ats_html bridge function in templater.py."""

    def test_produces_valid_html(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_contains_name(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "Alice Tester" in html

    def test_contains_semantic_elements(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "<header>" in html
        assert "<section" in html
        assert "<article>" in html
        assert "<h1>" in html
        assert "<h2>" in html

    def test_extracts_linkedin_from_social_networks(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "alice-tester" in html
        assert "LinkedIn" in html

    def test_extracts_github_from_social_networks(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "alicetest" in html
        assert "GitHub" in html

    def test_contains_contact_info(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "alice@example.com" in html
        assert "Boston, MA" in html

    def test_contains_experience_entries(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "BigCorp" in html
        assert "Staff Engineer" in html
        assert "Led platform team" in html

    def test_contains_education_entries(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.templater.templater import (
            render_ats_html,
        )

        model = _build_model(minimal_cv_yaml)
        html = render_ats_html(model)

        assert "MIT" in html
        assert "Computer Science" in html


# ---------------------------------------------------------------------------
# Tests: generate_ats_html in html.py
# ---------------------------------------------------------------------------


class TestGenerateAtsHtml:
    """Test ATS HTML file generation via html.py."""

    def test_generates_file(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.html import generate_ats_html

        model = _build_model(minimal_cv_yaml)
        result = generate_ats_html(model)

        assert result is not None
        assert result.exists()
        assert result.name.endswith("_ats.html")

    def test_file_contains_valid_html(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.html import generate_ats_html

        model = _build_model(minimal_cv_yaml)
        result = generate_ats_html(model)

        content = result.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Alice Tester" in content

    def test_output_path_derives_from_html_path(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.html import generate_ats_html

        model = _build_model(minimal_cv_yaml)
        result = generate_ats_html(model)

        # The ATS HTML path should be the standard HTML path with _ats suffix
        assert "_ats.html" in result.name
        # The stem should end with _ats
        assert result.stem.endswith("_ats")

    def test_skipped_when_dont_generate_true(self, minimal_cv_yaml: pathlib.Path):
        from anvilcv.vendor.rendercv.renderer.html import generate_ats_html

        model = _build_model(minimal_cv_yaml)
        result = generate_ats_html(model, dont_generate=True)

        assert result is None


# ---------------------------------------------------------------------------
# Tests: CLI --no-ats-html flag
# ---------------------------------------------------------------------------


class TestNoAtsHtmlFlag:
    """Test that the --no-ats-html flag is registered and functional.

    Reads the source file directly to verify the flag exists, avoiding
    any Python import that would trigger Typer's type hint resolution
    (which conflicts with parallel mock tests via xdist workers).
    """

    def test_flag_registered_in_source(self):
        """The render command source should define --no-ats-html."""
        import pathlib

        src = pathlib.Path(__file__).parents[3] / (
            "src/anvilcv/vendor/rendercv/cli/render_command/render_command.py"
        )
        content = src.read_text()
        assert '"--no-ats-html"' in content

    def test_flag_has_help_text(self):
        """The --no-ats-html option should have help text mentioning ATS."""
        import pathlib

        src = pathlib.Path(__file__).parents[3] / (
            "src/anvilcv/vendor/rendercv/cli/render_command/render_command.py"
        )
        content = src.read_text()
        # Find the help text near --no-ats-html
        idx = content.index('"--no-ats-html"')
        nearby = content[idx : idx + 200]
        assert "ATS" in nearby
