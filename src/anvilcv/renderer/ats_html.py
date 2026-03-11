"""ATS-first semantic HTML renderer.

Why:
    ATS systems parse HTML for resume content. Standard rendercv HTML is
    generated from Markdown and styled for visual presentation, which may
    not parse well. This renderer produces semantic HTML using <section>,
    <article>, <h1>-<h3> elements with all text in the DOM.
"""

from __future__ import annotations

import html
import pathlib
from typing import Any


def render_ats_html(cv_data: dict) -> str:
    """Render a CV data dictionary to ATS-optimized semantic HTML.

    Args:
        cv_data: The 'cv' section of an AnvilModel/RenderCVModel dict.

    Returns:
        Complete HTML5 document string.
    """
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_esc(cv_data.get('name', 'Resume'))}</title>",
        "<style>",
        _ats_css(),
        "</style>",
        "</head>",
        "<body>",
    ]

    # Header with contact info
    parts.append(_render_header(cv_data))

    # Sections
    sections = cv_data.get("sections", {})
    for section_name, section_data in sections.items():
        parts.append(_render_section(section_name, section_data))

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)


def generate_ats_html(
    cv_data: dict,
    output_path: pathlib.Path,
) -> pathlib.Path:
    """Generate an ATS HTML file from CV data.

    Args:
        cv_data: The 'cv' section of the model dict.
        output_path: Where to write the HTML file.

    Returns:
        Path to the written file.
    """
    html_content = render_ats_html(cv_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def _esc(text: Any) -> str:
    """HTML-escape a value."""
    if text is None:
        return ""
    return html.escape(str(text))


def _ats_css() -> str:
    """Minimal CSS for visual styling only — all content is in the DOM."""
    return """\
body {
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.5;
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
  color: #1a1a1a;
}
header { margin-bottom: 1.5rem; }
h1 { font-size: 1.5rem; margin: 0 0 0.25rem; }
h2 {
  font-size: 1.15rem; border-bottom: 1px solid #ccc;
  padding-bottom: 0.2rem; margin-top: 1.25rem;
}
h3 { font-size: 1rem; margin: 0.75rem 0 0.15rem; }
.contact { font-size: 0.9rem; color: #444; }
.contact span + span::before { content: " | "; }
article { margin-bottom: 0.75rem; }
.meta { font-size: 0.9rem; color: #555; }
ul { margin: 0.25rem 0; padding-left: 1.5rem; }
li { margin-bottom: 0.15rem; }
.skills-list { list-style: none; padding: 0; }
.skills-list li { display: inline; }
.skills-list li + li::before { content: " · "; }"""


def _render_header(cv_data: dict) -> str:
    """Render the header section with name and contact info."""
    parts = ["<header>"]
    name = cv_data.get("name", "")
    parts.append(f"<h1>{_esc(name)}</h1>")

    contact_items = []
    if cv_data.get("location"):
        contact_items.append(f"<span>{_esc(cv_data['location'])}</span>")
    if cv_data.get("email"):
        email = cv_data["email"]
        contact_items.append(f'<span><a href="mailto:{_esc(email)}">{_esc(email)}</a></span>')
    if cv_data.get("phone"):
        contact_items.append(f"<span>{_esc(cv_data['phone'])}</span>")
    if cv_data.get("website"):
        url = cv_data["website"]
        contact_items.append(f'<span><a href="{_esc(url)}">{_esc(url)}</a></span>')
    if cv_data.get("linkedin"):
        contact_items.append(f"<span>LinkedIn: {_esc(cv_data['linkedin'])}</span>")
    if cv_data.get("github"):
        contact_items.append(f"<span>GitHub: {_esc(cv_data['github'])}</span>")

    if contact_items:
        parts.append(f'<div class="contact">{"".join(contact_items)}</div>')

    parts.append("</header>")
    return "\n".join(parts)


def _render_section(name: str, data: Any) -> str:
    """Render a resume section with semantic markup."""
    heading = _format_section_name(name)
    parts = [f'<section id="{_esc(name)}">', f"<h2>{_esc(heading)}</h2>"]

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                parts.append(_render_entry(item))
            elif isinstance(item, str):
                parts.append(f"<p>{_esc(item)}</p>")
    elif isinstance(data, str):
        parts.append(f"<p>{_esc(data)}</p>")

    parts.append("</section>")
    return "\n".join(parts)


def _render_entry(entry: dict) -> str:
    """Render a single entry (experience, education, project, etc.)."""
    parts = ["<article>"]

    # Title line
    title_parts = []
    if entry.get("company"):
        title_parts.append(_esc(entry["company"]))
    if entry.get("institution"):
        title_parts.append(_esc(entry["institution"]))
    if entry.get("name"):
        title_parts.append(_esc(entry["name"]))

    if title_parts:
        parts.append(f"<h3>{', '.join(title_parts)}</h3>")

    # Meta line (position, degree, dates)
    meta_parts = []
    if entry.get("position"):
        meta_parts.append(_esc(entry["position"]))
    if entry.get("degree") and entry.get("area"):
        meta_parts.append(f"{_esc(entry['degree'])} in {_esc(entry['area'])}")
    elif entry.get("degree"):
        meta_parts.append(_esc(entry["degree"]))
    elif entry.get("area"):
        meta_parts.append(_esc(entry["area"]))

    date_str = _format_dates(entry)
    if date_str:
        meta_parts.append(date_str)

    if entry.get("location"):
        meta_parts.append(_esc(entry["location"]))

    if meta_parts:
        parts.append(f'<p class="meta">{" — ".join(meta_parts)}</p>')

    # Description / summary
    if entry.get("summary"):
        parts.append(f"<p>{_esc(entry['summary'])}</p>")

    # Highlights
    if entry.get("highlights"):
        parts.append("<ul>")
        for highlight in entry["highlights"]:
            parts.append(f"<li>{_esc(highlight)}</li>")
        parts.append("</ul>")

    # Skills entry (label: details)
    if entry.get("label"):
        details = entry.get("details", "")
        parts.append(f"<p><strong>{_esc(entry['label'])}:</strong> {_esc(details)}</p>")

    # URL
    if entry.get("url"):
        parts.append(f'<p><a href="{_esc(entry["url"])}">{_esc(entry["url"])}</a></p>')

    parts.append("</article>")
    return "\n".join(parts)


def _format_section_name(name: str) -> str:
    """Format a section key into a display heading."""
    return name.replace("_", " ").title()


def _format_dates(entry: dict) -> str:
    """Format date range from entry."""
    start = entry.get("start_date", "")
    end = entry.get("end_date", "")
    date = entry.get("date", "")

    if date:
        return _esc(str(date))
    if start and end:
        return f"{_esc(str(start))} — {_esc(str(end))}"
    if start:
        return _esc(str(start))
    return ""
