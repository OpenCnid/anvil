"""Tests for ATS-first semantic HTML renderer.

Why:
    The ATS HTML renderer must produce valid, semantic HTML with all text in
    the DOM. Tests verify: semantic element usage, contact info rendering,
    section/entry rendering, HTML escaping, and file generation.
"""

import pathlib

from anvilcv.renderer.ats_html import generate_ats_html, render_ats_html

SAMPLE_CV = {
    "name": "Jane Developer",
    "location": "New York, NY",
    "email": "jane@example.com",
    "phone": "+1-555-0100",
    "website": "https://jane.dev",
    "linkedin": "jane-developer",
    "github": "janedev",
    "sections": {
        "experience": [
            {
                "company": "TechCo",
                "position": "Senior Engineer",
                "start_date": "2021-06",
                "end_date": "present",
                "location": "NYC",
                "highlights": [
                    "Built real-time pipeline processing 500K events/sec",
                    "Led team of 5 engineers",
                ],
            },
            {
                "company": "StartupInc",
                "position": "Software Engineer",
                "start_date": "2019-01",
                "end_date": "2021-05",
                "highlights": [
                    "Developed REST API serving 1M+ requests/day",
                ],
            },
        ],
        "education": [
            {
                "institution": "Stanford",
                "area": "Computer Science",
                "degree": "MS",
                "start_date": "2017-09",
                "end_date": "2019-05",
            },
        ],
        "skills": [
            {"label": "Languages", "details": "Python, Go, Rust"},
            {"label": "Frameworks", "details": "FastAPI, React, Django"},
        ],
        "projects": [
            {
                "name": "open-source-tool",
                "date": "2023",
                "url": "https://github.com/janedev/open-source-tool",
                "highlights": ["CLI tool for YAML processing"],
            },
        ],
    },
}


class TestATSHTMLStructure:
    def test_produces_html5_doctype(self):
        html = render_ats_html(SAMPLE_CV)
        assert html.startswith("<!DOCTYPE html>")

    def test_has_html_lang(self):
        html = render_ats_html(SAMPLE_CV)
        assert '<html lang="en">' in html

    def test_has_meta_charset(self):
        html = render_ats_html(SAMPLE_CV)
        assert '<meta charset="utf-8">' in html

    def test_has_title(self):
        html = render_ats_html(SAMPLE_CV)
        assert "<title>Jane Developer</title>" in html

    def test_has_body(self):
        html = render_ats_html(SAMPLE_CV)
        assert "<body>" in html
        assert "</body>" in html


class TestATSHTMLHeader:
    def test_h1_name(self):
        html = render_ats_html(SAMPLE_CV)
        assert "<h1>Jane Developer</h1>" in html

    def test_contact_email(self):
        html = render_ats_html(SAMPLE_CV)
        assert "jane@example.com" in html
        assert "mailto:" in html

    def test_contact_location(self):
        html = render_ats_html(SAMPLE_CV)
        assert "New York, NY" in html

    def test_contact_phone(self):
        html = render_ats_html(SAMPLE_CV)
        assert "+1-555-0100" in html

    def test_contact_website(self):
        html = render_ats_html(SAMPLE_CV)
        assert "https://jane.dev" in html

    def test_contact_github(self):
        html = render_ats_html(SAMPLE_CV)
        assert "janedev" in html


class TestATSHTMLSemantic:
    def test_uses_section_elements(self):
        html = render_ats_html(SAMPLE_CV)
        assert '<section id="experience">' in html
        assert '<section id="education">' in html
        assert '<section id="skills">' in html

    def test_uses_h2_for_sections(self):
        html = render_ats_html(SAMPLE_CV)
        assert "<h2>Experience</h2>" in html
        assert "<h2>Education</h2>" in html
        assert "<h2>Skills</h2>" in html

    def test_uses_article_for_entries(self):
        html = render_ats_html(SAMPLE_CV)
        assert "<article>" in html
        assert "</article>" in html
        # Should have articles for each experience/education/project entry
        assert html.count("<article>") >= 5  # 2 exp + 1 edu + 2 skills + 1 proj

    def test_uses_h3_for_entry_titles(self):
        html = render_ats_html(SAMPLE_CV)
        assert "<h3>TechCo</h3>" in html
        assert "<h3>Stanford</h3>" in html

    def test_uses_ul_for_highlights(self):
        html = render_ats_html(SAMPLE_CV)
        assert "<ul>" in html
        assert "<li>" in html
        assert "500K events/sec" in html


class TestATSHTMLContent:
    def test_experience_position(self):
        html = render_ats_html(SAMPLE_CV)
        assert "Senior Engineer" in html

    def test_experience_dates(self):
        html = render_ats_html(SAMPLE_CV)
        assert "2021-06" in html
        assert "present" in html

    def test_education_degree(self):
        html = render_ats_html(SAMPLE_CV)
        assert "MS in Computer Science" in html

    def test_skills_label(self):
        html = render_ats_html(SAMPLE_CV)
        assert "Languages" in html
        assert "Python, Go, Rust" in html

    def test_project_url(self):
        html = render_ats_html(SAMPLE_CV)
        assert "https://github.com/janedev/open-source-tool" in html

    def test_project_name(self):
        html = render_ats_html(SAMPLE_CV)
        assert "open-source-tool" in html

    def test_all_highlights_present(self):
        html = render_ats_html(SAMPLE_CV)
        assert "500K events/sec" in html
        assert "Led team of 5 engineers" in html
        assert "1M+ requests/day" in html


class TestATSHTMLEscaping:
    def test_escapes_special_chars(self):
        cv = {
            "name": "Test <script>alert('xss')</script>",
            "sections": {},
        }
        html = render_ats_html(cv)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_escapes_in_highlights(self):
        cv = {
            "name": "Test",
            "sections": {
                "experience": [
                    {
                        "company": "Corp",
                        "highlights": ["Used <b>bold</b> & things"],
                    },
                ],
            },
        }
        html = render_ats_html(cv)
        assert "&lt;b&gt;" in html
        assert "&amp;" in html


class TestATSHTMLFile:
    def test_generates_file(self, tmp_path: pathlib.Path):
        output = tmp_path / "resume_ats.html"
        result = generate_ats_html(SAMPLE_CV, output)
        assert result == output
        assert output.exists()
        content = output.read_text()
        assert "<!DOCTYPE html>" in content

    def test_creates_parent_dirs(self, tmp_path: pathlib.Path):
        output = tmp_path / "nested" / "dir" / "resume_ats.html"
        generate_ats_html(SAMPLE_CV, output)
        assert output.exists()


class TestATSHTMLEdgeCases:
    def test_empty_sections(self):
        cv = {"name": "Empty", "sections": {}}
        html = render_ats_html(cv)
        assert "<h1>Empty</h1>" in html

    def test_minimal_cv(self):
        cv = {"name": "Min"}
        html = render_ats_html(cv)
        assert "<h1>Min</h1>" in html

    def test_section_name_formatting(self):
        cv = {
            "name": "Test",
            "sections": {"work_experience": [{"name": "Job"}]},
        }
        html = render_ats_html(cv)
        assert "<h2>Work Experience</h2>" in html

    def test_string_section(self):
        cv = {
            "name": "Test",
            "sections": {"summary": "A great engineer."},
        }
        html = render_ats_html(cv)
        assert "A great engineer." in html

    def test_no_contact_info(self):
        cv = {"name": "No Contact", "sections": {}}
        html = render_ats_html(cv)
        assert "<h1>No Contact</h1>" in html
        # No contact div should be rendered (class="contact" only in CSS)
        assert '<div class="contact">' not in html
