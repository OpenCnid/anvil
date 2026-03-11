"""Tests for ATS scoring rules and pipeline.

Why:
    100% coverage on scoring rules (P-01 through P-08, S-01 through S-08) is
    required per specs/success-criteria.md. Each rule is tested with known-good
    and known-bad inputs. The scorer pipeline is tested end-to-end on
    synthesized documents.
"""

import pathlib

import pytest

from anvilcv.schema.score_report import ScoreReport
from anvilcv.scoring.ats_scorer import (
    _calculate_category_score,
    _calculate_overall_score,
    score_extracted_document,
)
from anvilcv.scoring.parsability_checker import (
    check_p01_single_column,
    check_p02_no_embedded_images,
    check_p03_standard_fonts,
    check_p04_no_tables,
    check_p05_no_headers_footers,
    check_p06_text_extractability,
    check_p07_no_text_boxes,
    check_p08_standard_format,
    run_parsability_checks,
)
from anvilcv.scoring.section_detector import detect_sections
from anvilcv.scoring.structure_checker import (
    check_s01_contact_info,
    check_s02_experience_section,
    check_s03_education_section,
    check_s04_skills_section,
    check_s05_standard_headers,
    check_s06_chronological_dates,
    check_s07_machine_readable_dates,
    check_s08_resume_length,
    run_structure_checks,
)
from anvilcv.scoring.text_extractor import ExtractedDocument, TextElement

# --- Fixtures ---


def _good_resume_doc() -> ExtractedDocument:
    """A well-structured resume document (HTML-like, no position data)."""
    return ExtractedDocument(
        elements=[
            TextElement(text=line)
            for line in [
                "John Doe",
                "john@example.com | (555) 123-4567",
                "San Francisco, CA",
                "Experience",
                "Software Engineer at Acme Corp",
                "January 2020 - Present",
                "Built scalable microservices serving 1M+ requests/day",
                "Led migration from monolith to event-driven architecture",
                "Education",
                "MIT - BS Computer Science",
                "September 2016 - May 2020",
                "Skills",
                "Python, TypeScript, Go, Rust, Docker, Kubernetes",
            ]
        ],
        full_text=(
            "John Doe\njohn@example.com | (555) 123-4567\n"
            "San Francisco, CA\n"
            "Experience\n"
            "Software Engineer at Acme Corp\n"
            "January 2020 - Present\n"
            "Built scalable microservices serving 1M+ requests/day\n"
            "Led migration from monolith to event-driven architecture\n"
            "Education\n"
            "MIT - BS Computer Science\n"
            "September 2016 - May 2020\n"
            "Skills\n"
            "Python, TypeScript, Go, Rust, Docker, Kubernetes\n"
        ),
        page_count=1,
        source_type="html",
    )


def _pdf_resume_doc() -> ExtractedDocument:
    """A PDF resume with position data for column detection."""
    # Single column — all text at roughly x=72 (1 inch margin)
    elements = [
        TextElement(
            text="John Doe",
            x=72,
            y=700,
            width=200,
            height=14,
            font_name="Helvetica-Bold",
            font_size=14,
            page=1,
        ),
        TextElement(
            text="john@example.com",
            x=72,
            y=680,
            width=150,
            height=10,
            font_name="Helvetica",
            font_size=10,
            page=1,
        ),
        TextElement(
            text="Experience",
            x=72,
            y=640,
            width=100,
            height=12,
            font_name="Helvetica-Bold",
            font_size=12,
            page=1,
        ),
        TextElement(
            text="Software Engineer",
            x=72,
            y=620,
            width=150,
            height=10,
            font_name="Helvetica",
            font_size=10,
            page=1,
        ),
        TextElement(
            text="Built services",
            x=72,
            y=600,
            width=200,
            height=10,
            font_name="Helvetica",
            font_size=10,
            page=1,
        ),
        TextElement(
            text="Education",
            x=72,
            y=560,
            width=100,
            height=12,
            font_name="Helvetica-Bold",
            font_size=12,
            page=1,
        ),
        TextElement(
            text="Skills",
            x=72,
            y=500,
            width=100,
            height=12,
            font_name="Helvetica-Bold",
            font_size=12,
            page=1,
        ),
    ]
    return ExtractedDocument(
        elements=elements,
        full_text="\n".join(e.text for e in elements),
        page_count=1,
        source_type="pdf",
        fonts_used={"Helvetica", "Helvetica-Bold"},
    )


def _multi_column_doc() -> ExtractedDocument:
    """A PDF with multi-column layout."""
    elements = [
        TextElement(text="Left column", x=72, y=700, page=1),
        TextElement(text="Left content", x=72, y=680, page=1),
        TextElement(text="Right column", x=350, y=700, page=1),
        TextElement(text="Right content", x=350, y=680, page=1),
        TextElement(text="More left", x=72, y=660, page=1),
        TextElement(text="More right", x=350, y=660, page=1),
    ]
    return ExtractedDocument(
        elements=elements,
        full_text="\n".join(e.text for e in elements),
        page_count=1,
        source_type="pdf",
    )


def _empty_doc() -> ExtractedDocument:
    """An empty document with no text."""
    return ExtractedDocument(
        elements=[],
        full_text="",
        page_count=1,
        source_type="pdf",
    )


# --- Parsability Rules ---


class TestP01SingleColumn:
    def test_single_column_passes(self):
        result = check_p01_single_column(_pdf_resume_doc())
        assert result.status == "pass"

    def test_multi_column_warns(self):
        result = check_p01_single_column(_multi_column_doc())
        assert result.status == "warn"
        assert "multi-column" in result.detail.lower()

    def test_html_skipped(self):
        result = check_p01_single_column(_good_resume_doc())
        assert result.status == "pass"

    def test_empty_doc(self):
        result = check_p01_single_column(_empty_doc())
        assert result.status == "pass"


class TestP02NoEmbeddedImages:
    def test_text_extractable_passes(self):
        result = check_p02_no_embedded_images(_good_resume_doc())
        assert result.status == "pass"

    def test_image_only_pdf_fails(self):
        doc = ExtractedDocument(
            elements=[TextElement(text="a")],
            full_text="a",
            source_type="pdf",
            has_images=True,
        )
        assert check_p02_no_embedded_images(doc).status == "fail"

    def test_empty_text_fails(self):
        result = check_p02_no_embedded_images(_empty_doc())
        assert result.status == "fail"


class TestP03StandardFonts:
    def test_standard_fonts_pass(self):
        result = check_p03_standard_fonts(_pdf_resume_doc())
        assert result.status == "pass"

    def test_no_font_info_passes(self):
        result = check_p03_standard_fonts(_good_resume_doc())
        assert result.status == "pass"

    def test_non_standard_font_warns(self):
        doc = ExtractedDocument(
            elements=[],
            full_text="text",
            source_type="pdf",
            fonts_used={"CrazyCustomFont-Regular"},
        )
        result = check_p03_standard_fonts(doc)
        assert result.status == "warn"
        assert "CrazyCustomFont" in result.detail


class TestP04NoTables:
    def test_no_tables_passes(self):
        result = check_p04_no_tables(_good_resume_doc())
        assert result.status == "pass"

    def test_tables_warn(self):
        doc = ExtractedDocument(full_text="text", has_tables=True)
        result = check_p04_no_tables(doc)
        assert result.status == "warn"


class TestP05NoHeadersFooters:
    def test_passes_for_html(self):
        result = check_p05_no_headers_footers(_good_resume_doc())
        assert result.status == "pass"

    def test_passes_for_pdf(self):
        result = check_p05_no_headers_footers(_pdf_resume_doc())
        assert result.status == "pass"


class TestP06TextExtractability:
    def test_good_text_passes(self):
        result = check_p06_text_extractability(_good_resume_doc())
        assert result.status == "pass"

    def test_empty_text_fails(self):
        result = check_p06_text_extractability(_empty_doc())
        assert result.status == "fail"

    def test_very_little_text_warns(self):
        doc = ExtractedDocument(full_text="just a few words here")
        result = check_p06_text_extractability(doc)
        assert result.status == "warn"


class TestP07NoTextBoxes:
    def test_always_passes(self):
        result = check_p07_no_text_boxes(_good_resume_doc())
        assert result.status == "pass"


class TestP08StandardFormat:
    def test_html_passes(self):
        result = check_p08_standard_format(_good_resume_doc())
        assert result.status == "pass"

    def test_pdf_with_text_passes(self):
        result = check_p08_standard_format(_pdf_resume_doc())
        assert result.status == "pass"

    def test_empty_pdf_fails(self):
        result = check_p08_standard_format(_empty_doc())
        assert result.status == "fail"


class TestParsabilityRunner:
    def test_run_all_checks(self):
        checks = run_parsability_checks(_good_resume_doc())
        assert len(checks) == 8
        assert all(c.status == "pass" for c in checks)


# --- Section Detector ---


class TestSectionDetector:
    def test_detects_standard_sections(self):
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        assert sections.has_section("experience")
        assert sections.has_section("education")
        assert sections.has_section("skills")

    def test_no_sections_in_empty_doc(self):
        sections = detect_sections(_empty_doc())
        assert len(sections.sections) == 0

    def test_detects_variant_headers(self):
        doc = ExtractedDocument(
            full_text="Work History\nsome content\nAcademic Background\nmore\n",
            elements=[
                TextElement(text="Work History"),
                TextElement(text="some content"),
                TextElement(text="Academic Background"),
                TextElement(text="more"),
            ],
        )
        sections = detect_sections(doc)
        assert sections.has_section("experience")
        assert sections.has_section("education")

    def test_long_lines_not_headers(self):
        long_line = (
            "This is a very long line that should not be detected "
            "as a section header because it is way too long for that"
        )
        doc = ExtractedDocument(
            full_text=f"{long_line}\nExperience\n",
            elements=[
                TextElement(text=long_line),
                TextElement(text="Experience"),
            ],
        )
        sections = detect_sections(doc)
        assert sections.has_section("experience")
        assert len(sections.sections) == 1

    def test_get_section_returns_detected(self):
        """get_section returns a DetectedSection by canonical name."""
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        exp = sections.get_section("experience")
        assert exp is not None
        assert exp.name == "experience"

    def test_get_section_returns_none_for_missing(self):
        """get_section returns None for undetected sections."""
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        assert sections.get_section("nonexistent") is None

    def test_section_names_property(self):
        """section_names returns list of canonical names."""
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        names = sections.section_names
        assert isinstance(names, list)
        assert "experience" in names
        assert "education" in names

    def test_lines_ending_with_ellipsis_not_headers(self):
        """Lines ending with '...' are not treated as section headers."""
        doc = ExtractedDocument(
            full_text="Continue reading...\nExperience\n",
            elements=[
                TextElement(text="Continue reading..."),
                TextElement(text="Experience"),
            ],
        )
        sections = detect_sections(doc)
        assert sections.has_section("experience")
        assert len(sections.sections) == 1

    def test_lines_ending_with_semicolon_not_headers(self):
        """Lines ending with ';' are not treated as section headers."""
        doc = ExtractedDocument(
            full_text="some statement;\nSkills\n",
            elements=[
                TextElement(text="some statement;"),
                TextElement(text="Skills"),
            ],
        )
        sections = detect_sections(doc)
        assert sections.has_section("skills")
        assert len(sections.sections) == 1

    def test_decorated_header_stripped(self):
        """Headers with bullets/dashes/colons are still detected."""
        doc = ExtractedDocument(
            full_text="• Experience:\n",
            elements=[TextElement(text="• Experience:")],
        )
        sections = detect_sections(doc)
        assert sections.has_section("experience")

    def test_empty_after_stripping_not_matched(self):
        """Lines that are only decorators (no text after stripping) are skipped."""
        doc = ExtractedDocument(
            full_text="---\n• :\nExperience\n",
            elements=[
                TextElement(text="---"),
                TextElement(text="• :"),
                TextElement(text="Experience"),
            ],
        )
        sections = detect_sections(doc)
        assert sections.has_section("experience")
        assert len(sections.sections) == 1


# --- Structure Rules ---


class TestS01ContactInfo:
    def test_full_contact_passes(self):
        result = check_s01_contact_info(_good_resume_doc())
        assert result.status == "pass"

    def test_email_only_warns(self):
        doc = ExtractedDocument(full_text="john@example.com\nExperience\n")
        result = check_s01_contact_info(doc)
        assert result.status == "warn"
        assert "phone" in result.detail

    def test_no_contact_fails(self):
        doc = ExtractedDocument(full_text="Experience\nSoftware Engineer\n")
        result = check_s01_contact_info(doc)
        assert result.status == "fail"


class TestS02ExperienceSection:
    def test_present_passes(self):
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        result = check_s02_experience_section(sections)
        assert result.status == "pass"

    def test_missing_fails(self):
        from anvilcv.scoring.section_detector import SectionMap

        result = check_s02_experience_section(SectionMap())
        assert result.status == "fail"


class TestS03EducationSection:
    def test_present_passes(self):
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        result = check_s03_education_section(sections)
        assert result.status == "pass"

    def test_missing_fails(self):
        from anvilcv.scoring.section_detector import SectionMap

        result = check_s03_education_section(SectionMap())
        assert result.status == "fail"


class TestS04SkillsSection:
    def test_present_passes(self):
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        result = check_s04_skills_section(sections)
        assert result.status == "pass"

    def test_missing_warns(self):
        from anvilcv.scoring.section_detector import SectionMap

        result = check_s04_skills_section(SectionMap())
        assert result.status == "warn"


class TestS05StandardHeaders:
    def test_standard_headers_pass(self):
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        result = check_s05_standard_headers(sections)
        assert result.status == "pass"

    def test_no_headers_warns(self):
        from anvilcv.scoring.section_detector import SectionMap

        result = check_s05_standard_headers(SectionMap())
        assert result.status == "warn"


class TestS06ChronologicalDates:
    def test_reverse_chronological_passes(self):
        doc = ExtractedDocument(full_text="January 2024\nMarch 2022\nJune 2020\nSeptember 2018")
        result = check_s06_chronological_dates(doc)
        assert result.status == "pass"

    def test_insufficient_dates_passes(self):
        doc = ExtractedDocument(full_text="January 2024\nSome text")
        result = check_s06_chronological_dates(doc)
        assert result.status == "pass"

    def test_forward_chronological_warns(self):
        doc = ExtractedDocument(
            full_text=(
                "January 2018\nMarch 2019\nJune 2020\nSeptember 2021\nNovember 2022\nJanuary 2023"
            )
        )
        result = check_s06_chronological_dates(doc)
        assert result.status == "warn"


class TestS07MachineReadableDates:
    def test_full_month_names_pass(self):
        doc = ExtractedDocument(full_text="January 2024\nFebruary 2023")
        result = check_s07_machine_readable_dates(doc)
        assert result.status == "pass"

    def test_abbreviated_months_warn(self):
        doc = ExtractedDocument(full_text="Jan 2024\nFeb 2023")
        result = check_s07_machine_readable_dates(doc)
        assert result.status == "warn"

    def test_mixed_formats_warn(self):
        doc = ExtractedDocument(full_text="January 2024\nFeb 2023")
        result = check_s07_machine_readable_dates(doc)
        assert result.status == "warn"


class TestS08ResumeLength:
    def test_one_page_passes(self):
        doc = ExtractedDocument(page_count=1)
        result = check_s08_resume_length(doc)
        assert result.status == "pass"

    def test_two_pages_passes(self):
        doc = ExtractedDocument(page_count=2)
        result = check_s08_resume_length(doc)
        assert result.status == "pass"

    def test_three_pages_warns(self):
        doc = ExtractedDocument(page_count=3)
        result = check_s08_resume_length(doc)
        assert result.status == "warn"


class TestStructureRunner:
    def test_run_all_checks(self):
        doc = _good_resume_doc()
        sections = detect_sections(doc)
        checks = run_structure_checks(doc, sections)
        assert len(checks) == 8


# --- Score Calculation ---


class TestScoreCalculation:
    def test_all_pass_is_100(self):
        from anvilcv.schema.score_report import Check

        checks = [Check(name="test", status="pass", confidence="evidence_based") for _ in range(8)]
        assert _calculate_category_score(checks) == 100

    def test_all_fail_is_0(self):
        from anvilcv.schema.score_report import Check

        checks = [Check(name="test", status="fail", confidence="evidence_based") for _ in range(8)]
        assert _calculate_category_score(checks) == 0

    def test_warns_count_half(self):
        from anvilcv.schema.score_report import Check

        checks = [Check(name="test", status="warn", confidence="evidence_based") for _ in range(4)]
        assert _calculate_category_score(checks) == 50

    def test_overall_without_keywords(self):
        score = _calculate_overall_score(80, 60)
        # 80*0.55 + 60*0.45 = 44 + 27 = 71
        assert score == 71

    def test_overall_with_keywords(self):
        score = _calculate_overall_score(80, 60, 70)
        # 80*0.40 + 60*0.30 + 70*0.30 = 32 + 18 + 21 = 71
        assert score == 71

    def test_empty_checks(self):
        assert _calculate_category_score([]) == 0


# --- End-to-End Scorer ---


class TestATSScorer:
    def test_score_good_resume(self):
        doc = _good_resume_doc()
        report = score_extracted_document(doc, file_path="test.html")
        assert isinstance(report, ScoreReport)
        assert report.overall_score > 50
        assert report.parsability.score > 50
        assert report.structure.score > 50
        assert report.keyword_match is None

    def test_score_empty_document(self):
        doc = _empty_doc()
        report = score_extracted_document(doc, file_path="empty.pdf")
        assert report.overall_score < 80  # Not great but some rules still pass
        assert report.parsability.score < 80

    def test_score_pdf_resume(self):
        doc = _pdf_resume_doc()
        report = score_extracted_document(doc, file_path="resume.pdf")
        assert report.overall_score > 0
        assert len(report.parsability.checks) == 8
        assert len(report.structure.checks) == 8


# --- Text Extractor ---


class TestTextExtractor:
    def test_extract_from_html(self, tmp_path: pathlib.Path):
        from anvilcv.scoring.text_extractor import extract_from_html

        html = tmp_path / "test.html"
        html.write_text(
            "<html><body>"
            "<h1>John Doe</h1>"
            "<p>john@example.com</p>"
            "<h2>Experience</h2>"
            "<p>Software Engineer at Acme</p>"
            "</body></html>"
        )
        doc = extract_from_html(html)
        assert "John Doe" in doc.full_text
        assert "Experience" in doc.full_text
        assert doc.source_type == "html"

    def test_extract_html_with_tables(self, tmp_path: pathlib.Path):
        from anvilcv.scoring.text_extractor import extract_from_html

        html = tmp_path / "test.html"
        html.write_text("<html><body><table><tr><td>cell</td></tr></table></body></html>")
        doc = extract_from_html(html)
        assert doc.has_tables is True

    def test_extract_skips_script_style(self, tmp_path: pathlib.Path):
        from anvilcv.scoring.text_extractor import extract_from_html

        html = tmp_path / "test.html"
        html.write_text(
            "<html><head><style>body{color:red}</style></head>"
            "<body><script>alert('hi')</script><p>Visible</p></body></html>"
        )
        doc = extract_from_html(html)
        assert "Visible" in doc.full_text
        assert "alert" not in doc.full_text
        assert "color" not in doc.full_text

    def test_extract_unsupported_format(self, tmp_path: pathlib.Path):
        from anvilcv.scoring.text_extractor import extract_text

        txt = tmp_path / "test.txt"
        txt.write_text("hello")
        with pytest.raises(Exception, match="Unsupported"):
            extract_text(txt)

    def test_extract_missing_file(self, tmp_path: pathlib.Path):
        from anvilcv.scoring.text_extractor import extract_from_html

        with pytest.raises(Exception, match="not found"):
            extract_from_html(tmp_path / "nonexistent.html")
