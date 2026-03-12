// Devforge theme preamble — page setup, fonts, and helper functions.
#import "@preview/rendercv:0.2.0": *

#show: rendercv.with(
  date: datetime(
    year: {{ settings._resolved_current_date.year }},
    month: {{ settings._resolved_current_date.month }},
    day: {{ settings._resolved_current_date.day }},
  ),
  {% if design.page.size == "us-letter" %}
  page-size: "us-letter",
  {% else %}
  page-size: "a4",
  {% endif %}
  page-top-margin: {{ design.page.top_margin }},
  page-bottom-margin: {{ design.page.bottom_margin }},
  page-left-margin: {{ design.page.left_margin }},
  page-right-margin: {{ design.page.right_margin }},
  body-font-family: ("{{ design.typography.font_family.body }}", "Inter", "Source Sans 3"),
  body-font-size: {{ design.typography.font_size.body }},
  body-text-color: {{ design.colors.body.as_rgb() }},
  heading-font-family: ("{{ design.typography.font_family.body }}",),
  heading-font-size: {{ design.typography.font_size.section_title }},
  heading-text-color: {{ design.colors.section_titles.as_rgb() }},
  links-font-color: {{ design.colors.links.as_rgb() }},
  connections-font-size: {{ design.typography.font_size.connections }},
  connections-font-color: {{ design.colors.connections.as_rgb() }},
  {% if design.links.underline %}
  links-underline: true,
  {% else %}
  links-underline: false,
  {% endif %}
  show-external-link-icon: false,
  {% if design.page.show_footer %}
  show-footer: true,
  {% else %}
  show-footer: false,
  {% endif %}
  show-top-note: false,
  footer-font-color: {{ design.colors.footer.as_rgb() }},
  footer-text: [{{ cv._footer }}],
  top-note-text: [{{ cv._top_note }}],
  line-spacing: {{ design.typography.line_spacing }},
  text-alignment: "left",
  name-font-size: {{ design.typography.font_size.name }},
  name-bold: true,
  name-font-color: {{ design.colors.name.as_rgb() }},
  headline-font-size: {{ design.typography.font_size.headline }},
  headline-bold: false,
  headline-font-color: {{ design.colors.headline.as_rgb() }},
  header-alignment: "{{ design.header.alignment }}",
  space-between-name-and-connections: {{ design.header.space_below_name }},
  space-between-headline-and-connections: {{ design.header.space_below_headline }},
  space-between-connections: 12pt,
  connections-separator: "{{ design.header.connections_separator }}",
  section-title-type: "with-partial-line",
  section-title-font-weight: 600,
  section-title-line-thickness: 2pt,
  section-title-space-above: {{ design.section_titles.space_above }},
  section-title-space-below: {{ design.section_titles.space_below }},
  allow-section-page-break: true,
  space-between-regular-entries: {{ design.entries.space_between_regular }},
  space-between-text-based-entries: {{ design.entries.space_between_text }},
  allow-entry-page-break: true,
  date-and-location-column-width: 0pt,
  space-between-entry-date-and-main-columns: 0pt,
  entry-side-space: 0pt,
  short-second-row: false,
  show-time-spans: false,
  highlight-bullet: "{{ design.entries.highlight_bullet }}",
  highlight-left-margin: {{ design.entries.highlight_left_margin }},
  highlight-bullet-font-size: 10pt,
  highlight-top-spacing: 2pt,
  highlight-spacing-between: 2pt,
)

// Devforge overrides: uppercase section titles with accent underline
#show heading.where(level: 2): it => {
  v({{ design.section_titles.space_above }})
  text(
    {{ design.typography.font_size.section_title }},
    weight: 600,
    tracking: 0.08em,
    fill: {{ design.colors.section_titles.as_rgb() }},
    upper(it.body),
  )
  v(4pt)
  line(length: {{ design.section_titles.underline_width }}, stroke: 2pt + {{ design.colors.accent.as_rgb() }})
  v({{ design.section_titles.space_below }})
}

// Skill chip function
#let skill-chip(content) = box(
  fill: {{ design.colors.chip_background.as_rgb() }},
  stroke: 1pt + {{ design.colors.chip_border.as_rgb() }},
  radius: {{ design.skill_chips.border_radius }},
  inset: (x: {{ design.skill_chips.padding_x }}, y: {{ design.skill_chips.padding_y }}),
  text(
    {{ design.skill_chips.font_size }},
    weight: 500,
    font: "{{ design.typography.font_family.mono }}",
    fill: {{ design.colors.chip_text.as_rgb() }},
    content,
  ),
)

// Devforge entry header: title left, date right, subtitle left, location right
#let devforge-entry(
  title: none,
  subtitle: none,
  date: none,
  location: none,
  body,
) = {
  // Line 1: title + date
  if title != none {
    grid(
      columns: (1fr, auto),
      align: (left, right),
      text({{ design.typography.font_size.entry_title }}, weight: 600, fill: {{ design.colors.body.as_rgb() }}, title),
      if date != none {
        text({{ design.typography.font_size.meta }}, fill: {{ design.colors.muted.as_rgb() }}, date)
      },
    )
  }
  // Line 2: subtitle + location
  if subtitle != none or location != none {
    v(2pt)
    grid(
      columns: (1fr, auto),
      align: (left, right),
      if subtitle != none {
        text({{ design.typography.font_size.entry_subtitle }}, style: "italic", fill: {{ design.colors.headline.as_rgb() }}, subtitle)
      },
      if location != none {
        text({{ design.typography.font_size.meta }}, fill: {{ design.colors.muted.as_rgb() }}, location)
      },
    )
  }
  // Body content (highlights, summary)
  body
}

// Metadata line for GitHub project metadata
#let meta-line(..components) = {
  let items = components.pos().filter(x => x != none and x != "")
  if items.len() > 0 {
    v(2pt)
    text(
      {{ design.typography.font_size.meta }},
      font: "{{ design.typography.font_family.mono }}",
      fill: {{ design.colors.muted.as_rgb() }},
      items.join(" · "),
    )
  }
}
