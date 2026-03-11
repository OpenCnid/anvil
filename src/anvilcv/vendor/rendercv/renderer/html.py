import pathlib

from rendercv.schema.models.rendercv_model import RenderCVModel

from .path_resolver import resolve_rendercv_file_path
from .templater.templater import render_ats_html as render_ats_html_content
from .templater.templater import render_html


def generate_html(
    rendercv_model: RenderCVModel, markdown_path: pathlib.Path | None
) -> pathlib.Path | None:
    """Generate HTML file from Markdown source with styling.

    Why:
        HTML format enables web hosting and sharing CVs online. Converts
        Markdown to HTML body and wraps with CSS styling and metadata.

    Args:
        rendercv_model: CV model for path resolution and rendering context.
        markdown_path: Path to Markdown source file.

    Returns:
        Path to generated HTML file, or None if generation disabled.
    """
    if (
        rendercv_model.settings.render_command.dont_generate_html
        or markdown_path is None
    ):
        return None
    html_path = resolve_rendercv_file_path(
        rendercv_model, rendercv_model.settings.render_command.html_path
    )
    html_contents = render_html(
        rendercv_model, markdown_path.read_text(encoding="utf-8")
    )
    html_path.write_text(html_contents, encoding="utf-8")
    return html_path


def generate_ats_html(
    rendercv_model: RenderCVModel,
    dont_generate: bool = False,
) -> pathlib.Path | None:
    """Generate ATS-optimized semantic HTML file alongside standard HTML.

    Why:
        ATS systems parse HTML for resume content. Standard HTML is derived
        from Markdown and styled for visual presentation, which may not parse
        well. This generates a separate semantic HTML file using <section>,
        <article>, <h1>-<h3> elements with all text in the DOM.

    Args:
        rendercv_model: CV model for rendering and path resolution.
        dont_generate: If True, skip ATS HTML generation.

    Returns:
        Path to generated ATS HTML file, or None if generation skipped.
    """
    if dont_generate:
        return None

    # Derive ATS HTML path from standard HTML path: name_ats.html
    html_path = resolve_rendercv_file_path(
        rendercv_model, rendercv_model.settings.render_command.html_path
    )
    ats_html_path = html_path.with_name(html_path.stem + "_ats.html")

    ats_html_contents = render_ats_html_content(rendercv_model)
    ats_html_path.parent.mkdir(parents=True, exist_ok=True)
    ats_html_path.write_text(ats_html_contents, encoding="utf-8")
    return ats_html_path
