"""Tests for text_extractor PDF extraction and dispatch.

Why:
    Covers extract_from_pdf (lines 56-112) and extract_text dispatch
    (lines 177, 179) which are not covered in test_scoring.py.
"""

import pathlib
from unittest.mock import MagicMock, patch

import pytest

from anvilcv.exceptions import AnvilUserError
from anvilcv.scoring.text_extractor import (
    ExtractedDocument,
    extract_text,
)


class TestExtractFromPdf:
    """Tests for extract_from_pdf covering lines 56-112."""

    def test_pdf_file_not_found(self, tmp_path: pathlib.Path):
        """Cover line 60: missing file raises AnvilUserError."""
        from anvilcv.scoring.text_extractor import extract_from_pdf

        with pytest.raises(AnvilUserError, match="not found"):
            extract_from_pdf(tmp_path / "nonexistent.pdf")

    @patch("pdfminer.high_level.extract_pages")
    def test_extract_pdf_basic(self, mock_extract_pages, tmp_path: pathlib.Path):
        """Cover lines 56-112: full PDF extraction with text boxes."""
        from pdfminer.layout import LTChar, LTFigure, LTTextBox, LTTextLine

        from anvilcv.scoring.text_extractor import extract_from_pdf

        pdf_path = tmp_path / "resume.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        # Build mock pdfminer objects with correct types
        mock_char = MagicMock(spec=LTChar)
        mock_char.fontname = "Helvetica"
        mock_char.size = 12.0

        mock_line = MagicMock(spec=LTTextLine)
        mock_line.get_text.return_value = "John Doe\n"
        mock_line.x0 = 72.0
        mock_line.y0 = 700.0
        mock_line.x1 = 200.0
        mock_line.y1 = 712.0
        mock_line.__iter__ = lambda self: iter([mock_char])

        mock_textbox = MagicMock(spec=LTTextBox)
        mock_textbox.__iter__ = lambda self: iter([mock_line])

        mock_figure = MagicMock(spec=LTFigure)

        mock_page = MagicMock()
        mock_page.__iter__ = lambda self: iter([mock_textbox, mock_figure])

        mock_extract_pages.return_value = [mock_page]
        doc = extract_from_pdf(pdf_path)

        assert doc.source_type == "pdf"
        assert doc.page_count == 1
        assert doc.has_images is True  # LTFigure detected
        assert len(doc.elements) == 1
        assert doc.elements[0].text == "John Doe"
        assert doc.elements[0].font_name == "Helvetica"
        assert doc.elements[0].font_size == 12.0
        assert "Helvetica" in doc.fonts_used
        assert "John Doe" in doc.full_text

    @patch("pdfminer.high_level.extract_pages")
    def test_extract_pdf_empty_text_skipped(self, mock_extract_pages, tmp_path: pathlib.Path):
        """Cover line 83-84: empty text lines are skipped."""
        from pdfminer.layout import LTTextBox, LTTextLine

        from anvilcv.scoring.text_extractor import extract_from_pdf

        pdf_path = tmp_path / "resume.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_line = MagicMock(spec=LTTextLine)
        mock_line.get_text.return_value = "   \n"

        mock_textbox = MagicMock(spec=LTTextBox)
        mock_textbox.__iter__ = lambda self: iter([mock_line])

        mock_page = MagicMock()
        mock_page.__iter__ = lambda self: iter([mock_textbox])

        mock_extract_pages.return_value = [mock_page]
        doc = extract_from_pdf(pdf_path)

        assert len(doc.elements) == 0
        assert doc.full_text == ""

    @patch("pdfminer.high_level.extract_pages")
    def test_extract_pdf_no_pages(self, mock_extract_pages, tmp_path: pathlib.Path):
        """Cover line 115: page_count defaults to max(0, 1) = 1."""
        from anvilcv.scoring.text_extractor import extract_from_pdf

        pdf_path = tmp_path / "empty.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_extract_pages.return_value = []  # No pages
        doc = extract_from_pdf(pdf_path)

        assert doc.page_count == 1  # max(0, 1)
        assert doc.source_type == "pdf"


class TestExtractTextDispatch:
    """Tests for extract_text auto-detection (lines 177, 179)."""

    def test_dispatch_to_html(self, tmp_path: pathlib.Path):
        """Cover line 179: .html dispatches to extract_from_html."""
        html_file = tmp_path / "resume.html"
        html_file.write_text("<html><body><p>Hello</p></body></html>")

        doc = extract_text(html_file)
        assert doc.source_type == "html"
        assert "Hello" in doc.full_text

    def test_dispatch_to_htm(self, tmp_path: pathlib.Path):
        """Cover line 179: .htm also dispatches to extract_from_html."""
        htm_file = tmp_path / "resume.htm"
        htm_file.write_text("<html><body><p>World</p></body></html>")

        doc = extract_text(htm_file)
        assert doc.source_type == "html"

    @patch("anvilcv.scoring.text_extractor.extract_from_pdf")
    def test_dispatch_to_pdf(self, mock_pdf, tmp_path: pathlib.Path):
        """Cover line 177: .pdf dispatches to extract_from_pdf."""
        mock_pdf.return_value = ExtractedDocument(source_type="pdf", full_text="test")
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"%PDF fake")

        doc = extract_text(pdf_file)
        assert doc.source_type == "pdf"
        mock_pdf.assert_called_once_with(pdf_file)

    def test_dispatch_unsupported(self, tmp_path: pathlib.Path):
        """Cover lines 181-186: unsupported format raises error."""
        docx_file = tmp_path / "resume.docx"
        docx_file.write_bytes(b"fake")

        with pytest.raises(AnvilUserError, match="Unsupported"):
            extract_text(docx_file)
