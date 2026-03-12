"""Devforge theme Pydantic model.

Why:
    Devforge is a single-column, ATS-safe resume theme for software engineers.
    Unlike classic's two-column entry layout, devforge places dates inline with
    titles and renders skills as visual chips. The model defines all configurable
    design tokens (colors, typography, spacing) used by the Jinja2 templates.
"""

from __future__ import annotations

from typing import Literal

import pydantic

from anvilcv.vendor.rendercv.schema.models.base import BaseModelWithoutExtraKeys
from anvilcv.vendor.rendercv.schema.models.design.classic_theme import (
    Color,
)

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class DevforgePage(BaseModelWithoutExtraKeys):
    size: Literal["us-letter", "a4"] = pydantic.Field(
        default="us-letter",
        description="Page size.",
    )
    top_margin: str = pydantic.Field(
        default="0.6in",
        description="Top margin.",
    )
    bottom_margin: str = pydantic.Field(
        default="0.6in",
        description="Bottom margin.",
    )
    left_margin: str = pydantic.Field(
        default="0.7in",
        description="Left margin.",
    )
    right_margin: str = pydantic.Field(
        default="0.7in",
        description="Right margin.",
    )
    show_footer: bool = pydantic.Field(
        default=True,
        description="Show page footer with name and page number.",
    )


class DevforgeFontFamily(BaseModelWithoutExtraKeys):
    body: str = pydantic.Field(
        default="IBM Plex Sans",
        description="Body and heading font.",
    )
    mono: str = pydantic.Field(
        default="IBM Plex Mono",
        description="Monospace font for skill chips and metadata.",
    )


class DevforgeFontSize(BaseModelWithoutExtraKeys):
    name: str = pydantic.Field(default="24pt")
    headline: str = pydantic.Field(default="11pt")
    connections: str = pydantic.Field(default="9pt")
    section_title: str = pydantic.Field(default="12pt")
    entry_title: str = pydantic.Field(default="10.5pt")
    entry_subtitle: str = pydantic.Field(default="10pt")
    body: str = pydantic.Field(default="10pt")
    meta: str = pydantic.Field(default="9pt")
    chip: str = pydantic.Field(default="8.5pt")
    footer: str = pydantic.Field(default="8pt")


class DevforgeTypography(BaseModelWithoutExtraKeys):
    font_family: DevforgeFontFamily = pydantic.Field(
        default_factory=DevforgeFontFamily,
    )
    font_size: DevforgeFontSize = pydantic.Field(
        default_factory=DevforgeFontSize,
    )
    line_spacing: float = pydantic.Field(
        default=1.35,
        description="Body text line height.",
    )


class DevforgeColors(BaseModelWithoutExtraKeys):
    body: Color = pydantic.Field(default=Color("rgb(26, 26, 46)"))
    name: Color = pydantic.Field(default=Color("rgb(26, 26, 46)"))
    headline: Color = pydantic.Field(default=Color("rgb(74, 74, 104)"))
    connections: Color = pydantic.Field(default=Color("rgb(74, 74, 104)"))
    section_titles: Color = pydantic.Field(default=Color("rgb(26, 26, 46)"))
    accent: Color = pydantic.Field(default=Color("rgb(37, 99, 235)"))
    links: Color = pydantic.Field(default=Color("rgb(37, 99, 235)"))
    muted: Color = pydantic.Field(default=Color("rgb(122, 122, 148)"))
    chip_background: Color = pydantic.Field(default=Color("rgb(240, 244, 255)"))
    chip_border: Color = pydantic.Field(default=Color("rgb(219, 228, 255)"))
    chip_text: Color = pydantic.Field(default=Color("rgb(37, 99, 235)"))
    footer: Color = pydantic.Field(default=Color("rgb(122, 122, 148)"))


class DevforgeSectionTitles(BaseModelWithoutExtraKeys):
    underline_width: str = pydantic.Field(
        default="40pt",
        description="Width of the accent underline below section titles.",
    )
    space_above: str = pydantic.Field(
        default="14pt",
        description="Vertical space above section titles.",
    )
    space_below: str = pydantic.Field(
        default="8pt",
        description="Vertical space below section title underline.",
    )


class DevforgeEntries(BaseModelWithoutExtraKeys):
    space_between_regular: str = pydantic.Field(
        default="12pt",
        description="Space between regular entries (experience, education, etc.).",
    )
    space_between_text: str = pydantic.Field(
        default="4pt",
        description="Space between text-based entries (bullet, numbered, text).",
    )
    highlight_bullet: str = pydantic.Field(
        default="•",
        description="Bullet character for highlights.",
    )
    highlight_left_margin: str = pydantic.Field(
        default="12pt",
        description="Left margin for highlight bullet lists.",
    )


class DevforgeSections(BaseModelWithoutExtraKeys):
    """Section-level settings required by the rendercv model_processor pipeline."""

    show_time_spans_in: list[str] = pydantic.Field(
        default_factory=list,
        description="Section names where time spans should be shown.",
    )


class DevforgeSkillChips(BaseModelWithoutExtraKeys):
    enabled: bool = pydantic.Field(
        default=True,
        description="Enable skill chip rendering in skills sections.",
    )
    border_radius: str = pydantic.Field(default="3pt")
    font_size: str = pydantic.Field(default="8.5pt")
    padding_x: str = pydantic.Field(default="4pt")
    padding_y: str = pydantic.Field(default="1.5pt")
    gap: str = pydantic.Field(default="4pt")


class DevforgeLinks(BaseModelWithoutExtraKeys):
    underline: bool = pydantic.Field(
        default=True,
        description="Underline hyperlinks.",
    )
    show_external_link_icon: bool = pydantic.Field(
        default=False,
        description="Show external link icon next to URLs.",
    )


class DevforgeConnections(BaseModelWithoutExtraKeys):
    """Connection display settings required by the rendercv compute_connections pipeline."""

    show_icons: bool = pydantic.Field(default=False)
    hyperlink: bool = pydantic.Field(default=True)
    display_urls_instead_of_usernames: bool = pydantic.Field(default=False)
    phone_number_format: str = pydantic.Field(default="national")
    separator: str = pydantic.Field(default=" · ")
    space_between_connections: str = pydantic.Field(default="12pt")


class DevforgeHeader(BaseModelWithoutExtraKeys):
    alignment: Literal["left", "center"] = pydantic.Field(
        default="left",
        description="Header text alignment.",
    )
    space_below_name: str = pydantic.Field(default="4pt")
    space_below_headline: str = pydantic.Field(default="4pt")
    space_below_connections: str = pydantic.Field(default="20pt")
    connections_separator: str = pydantic.Field(default=" · ")
    connections: DevforgeConnections = pydantic.Field(
        default_factory=DevforgeConnections,
    )


# ---------------------------------------------------------------------------
# Devforge-specific template defaults
# ---------------------------------------------------------------------------


class DevforgeOneLineEntry(BaseModelWithoutExtraKeys):
    main_column: str = pydantic.Field(default="**LABEL:** DETAILS")


class DevforgeEducationEntry(BaseModelWithoutExtraKeys):
    main_column: str = pydantic.Field(
        default="**INSTITUTION**\n*DEGREE_WITH_AREA*\nSUMMARY\nHIGHLIGHTS",
    )
    degree_column: str | None = pydantic.Field(default=None)
    date_and_location_column: str = pydantic.Field(default="DATE\nLOCATION")


class DevforgeNormalEntry(BaseModelWithoutExtraKeys):
    main_column: str = pydantic.Field(
        default="**NAME**\nSUMMARY\nHIGHLIGHTS",
    )
    date_and_location_column: str = pydantic.Field(default="DATE\nLOCATION")


class DevforgeExperienceEntry(BaseModelWithoutExtraKeys):
    main_column: str = pydantic.Field(
        default="**COMPANY**\n*POSITION*\nSUMMARY\nHIGHLIGHTS",
    )
    date_and_location_column: str = pydantic.Field(default="DATE\nLOCATION")


class DevforgePublicationEntry(BaseModelWithoutExtraKeys):
    main_column: str = pydantic.Field(
        default="**TITLE**\nAUTHORS\nSUMMARY\nURL (JOURNAL)",
    )
    date_and_location_column: str = pydantic.Field(default="DATE")


class DevforgeTemplates(BaseModelWithoutExtraKeys):
    footer: str = pydantic.Field(default="*NAME — PAGE_NUMBER/TOTAL_PAGES*")
    top_note: str = pydantic.Field(default="*LAST_UPDATED CURRENT_DATE*")
    single_date: str = pydantic.Field(default="MONTH_ABBREVIATION YEAR")
    date_range: str = pydantic.Field(default="START_DATE – END_DATE")
    time_span: str = pydantic.Field(
        default="HOW_MANY_YEARS YEARS HOW_MANY_MONTHS MONTHS",
    )
    one_line_entry: DevforgeOneLineEntry = pydantic.Field(
        default_factory=DevforgeOneLineEntry,
    )
    education_entry: DevforgeEducationEntry = pydantic.Field(
        default_factory=DevforgeEducationEntry,
    )
    normal_entry: DevforgeNormalEntry = pydantic.Field(
        default_factory=DevforgeNormalEntry,
    )
    experience_entry: DevforgeExperienceEntry = pydantic.Field(
        default_factory=DevforgeExperienceEntry,
    )
    publication_entry: DevforgePublicationEntry = pydantic.Field(
        default_factory=DevforgePublicationEntry,
    )


# ---------------------------------------------------------------------------
# Main theme model
# ---------------------------------------------------------------------------


class DevforgeTheme(BaseModelWithoutExtraKeys):
    """Devforge: clean, modern, developer-focused resume theme.

    Single-column layout with inline dates, accent-underlined section headers,
    and skill chip rendering. Designed for ATS compatibility.
    """

    theme: Literal["devforge"] = "devforge"
    page: DevforgePage = pydantic.Field(default_factory=DevforgePage)
    colors: DevforgeColors = pydantic.Field(default_factory=DevforgeColors)
    typography: DevforgeTypography = pydantic.Field(
        default_factory=DevforgeTypography,
    )
    links: DevforgeLinks = pydantic.Field(default_factory=DevforgeLinks)
    header: DevforgeHeader = pydantic.Field(default_factory=DevforgeHeader)
    section_titles: DevforgeSectionTitles = pydantic.Field(
        default_factory=DevforgeSectionTitles,
    )
    sections: DevforgeSections = pydantic.Field(default_factory=DevforgeSections)
    entries: DevforgeEntries = pydantic.Field(default_factory=DevforgeEntries)
    skill_chips: DevforgeSkillChips = pydantic.Field(
        default_factory=DevforgeSkillChips,
    )
    templates: DevforgeTemplates = pydantic.Field(
        default_factory=DevforgeTemplates,
    )
