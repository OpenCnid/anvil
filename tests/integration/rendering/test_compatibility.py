"""Compatibility corpus tests for the render pipeline.

Why:
    These tests verify that `anvil render` (via the vendored rendercv pipeline)
    can successfully process YAML files across all themes and entry types.
    We compare Typst, Markdown, and HTML outputs (NOT PDF/PNG — binary outputs
    are non-deterministic per spec).

    Tests use the corpus files in tests/corpus/ which cover:
    - All 5 built-in themes (classic, sb2nov, engineeringresumes, moderncv, engineeringclassic)
    - All entry types (text, education, experience, projects, publications,
      skills, one_line, bullet)
    - Edge cases (minimal CV, full CV with all types)
"""

import pathlib

import pytest

from anvilcv.vendor.rendercv.schema.rendercv_model_builder import (
    build_rendercv_dictionary_and_model,
)

CORPUS_DIR = pathlib.Path(__file__).parent.parent.parent / "corpus"


def _get_corpus_files() -> list[pathlib.Path]:
    """Collect all YAML files in the corpus directory."""
    if not CORPUS_DIR.exists():
        return []
    files = sorted(CORPUS_DIR.glob("*.yaml"))
    return files


def _build_model(yaml_path: pathlib.Path):
    """Build a rendercv model from a YAML file."""
    yaml_content = yaml_path.read_text(encoding="utf-8")
    return build_rendercv_dictionary_and_model(
        yaml_content,
        input_file_path=yaml_path,
    )


class TestCorpusValidation:
    """Verify all corpus files parse and validate successfully."""

    @pytest.mark.parametrize(
        "yaml_file",
        _get_corpus_files(),
        ids=[f.stem for f in _get_corpus_files()],
    )
    def test_corpus_file_validates(self, yaml_file: pathlib.Path):
        """Each corpus file must parse into a valid RenderCVModel."""
        _, model = _build_model(yaml_file)
        assert model is not None
        assert model.cv.name is not None

    @pytest.mark.parametrize(
        "yaml_file",
        _get_corpus_files(),
        ids=[f.stem for f in _get_corpus_files()],
    )
    def test_corpus_file_has_sections(self, yaml_file: pathlib.Path):
        """Each corpus file must have at least one section."""
        _, model = _build_model(yaml_file)
        assert model.cv.sections is not None
        # sections is a list of SectionContents which have a title
        assert len(model.cv.sections) > 0


class TestTypstGeneration:
    """Verify Typst source generation for all corpus files."""

    @pytest.mark.parametrize(
        "yaml_file",
        _get_corpus_files(),
        ids=[f.stem for f in _get_corpus_files()],
    )
    def test_generates_typst(self, yaml_file: pathlib.Path, tmp_path: pathlib.Path):
        """Each corpus file must produce valid Typst output."""
        from anvilcv.vendor.rendercv.renderer.typst import generate_typst

        _, model = _build_model(yaml_file)
        # Override output folder to tmp_path
        model.settings.render_command.output_folder = tmp_path

        typst_path = generate_typst(model)
        assert typst_path is not None
        assert typst_path.exists()
        content = typst_path.read_text()
        assert len(content) > 100
        # Typst files should contain the CV name
        assert model.cv.name in content


class TestMarkdownGeneration:
    """Verify Markdown generation for all corpus files."""

    @pytest.mark.parametrize(
        "yaml_file",
        _get_corpus_files(),
        ids=[f.stem for f in _get_corpus_files()],
    )
    def test_generates_markdown(self, yaml_file: pathlib.Path, tmp_path: pathlib.Path):
        """Each corpus file must produce valid Markdown output."""
        from anvilcv.vendor.rendercv.renderer.markdown import generate_markdown

        _, model = _build_model(yaml_file)
        model.settings.render_command.output_folder = tmp_path

        md_path = generate_markdown(model)
        assert md_path is not None
        assert md_path.exists()
        content = md_path.read_text()
        assert len(content) > 50
        assert model.cv.name in content


class TestHTMLGeneration:
    """Verify HTML generation for all corpus files."""

    @pytest.mark.parametrize(
        "yaml_file",
        _get_corpus_files(),
        ids=[f.stem for f in _get_corpus_files()],
    )
    def test_generates_html(self, yaml_file: pathlib.Path, tmp_path: pathlib.Path):
        """Each corpus file must produce valid HTML output."""
        from anvilcv.vendor.rendercv.renderer.html import generate_html
        from anvilcv.vendor.rendercv.renderer.markdown import generate_markdown

        _, model = _build_model(yaml_file)
        model.settings.render_command.output_folder = tmp_path

        md_path = generate_markdown(model)
        html_path = generate_html(model, md_path)

        if html_path is not None:
            assert html_path.exists()
            content = html_path.read_text()
            assert "<html" in content or "<HTML" in content
            assert model.cv.name in content


class TestThemeCoverage:
    """Verify we have corpus files for all built-in themes."""

    def test_has_classic_theme(self):
        files = [f.stem for f in _get_corpus_files()]
        assert any("classic" in f for f in files)

    def test_has_sb2nov_theme(self):
        files = [f.stem for f in _get_corpus_files()]
        assert any("sb2nov" in f for f in files)

    def test_has_engineeringresumes_theme(self):
        files = [f.stem for f in _get_corpus_files()]
        assert any("engineeringresumes" in f for f in files)

    def test_has_moderncv_theme(self):
        files = [f.stem for f in _get_corpus_files()]
        assert any("moderncv" in f for f in files)

    def test_has_engineeringclassic_theme(self):
        files = [f.stem for f in _get_corpus_files()]
        assert any("engineeringclassic" in f for f in files)

    def test_corpus_has_minimum_files(self):
        """Corpus should have at least 5 files (one per theme)."""
        files = _get_corpus_files()
        assert len(files) >= 5
