# Devforge Theme — Visual Design Specification

**Feature:** F-ANV-07 (Modern Engineer Theme)
**Status:** Design spec (prerequisite for implementation)
**Target:** Software engineers, DevOps/SRE, AI/ML engineers, tech leads

## Design Philosophy

Devforge is a single-column, ATS-safe resume theme that blends the clean readability of a GitHub README with the structured whitespace of Notion. It avoids decoration for decoration's sake. Every visual element serves information hierarchy or scannability. The aesthetic is: professional, modern, technically literate — without being flashy.

**Non-goals:** Multi-column layouts, sidebars, icons for section headers, color gradients, background patterns, decorative borders. These harm ATS parsing and add visual noise without improving information density.

---

## 1. Layout Grid

### Single-Column Structure

```
+----------------------------------------------------------+
|                    [top margin: 0.6in]                    |
|  [left margin: 0.7in]                  [right margin: 0.7in]  |
|                                                          |
|  HEADER (name, headline, connections)                    |
|  ────────────────────────────────────                    |
|  SECTION 1                                               |
|    Entry 1                                               |
|    Entry 2                                               |
|  ────────────────────────────────────                    |
|  SECTION 2                                               |
|    Entry 1                                               |
|  ...                                                     |
|                                                          |
|                    [bottom margin: 0.6in]                 |
+----------------------------------------------------------+
```

### Page Dimensions

| Property | Value | Rationale |
|----------|-------|-----------|
| Page size | `us-letter` (default), `a4` (supported) | US-letter for North American job market; A4 for international |
| Top margin | `0.6in` | Slightly tighter than classic (0.7in) to maximize content area |
| Bottom margin | `0.6in` | Matches top margin |
| Left margin | `0.7in` | Standard professional margin |
| Right margin | `0.7in` | Matches left margin |
| Content width | `7.1in` (letter) / `5.87in` (A4) | Derived: page width minus left and right margins |

### Content Regions

The page is a single column. No sidebar, no two-column date layout. Dates and locations appear inline with entry headers (see Entry Layouts, section 8) rather than in a separate right-aligned column. This is a deliberate departure from the rendercv classic theme's two-column entry layout — it improves ATS parsing reliability and simplifies the visual rhythm.

---

## 2. Typography

### Font Stack

Devforge uses system fonts for maximum cross-platform compatibility and zero font-loading latency. No custom webfonts, no Google Fonts dependency.

| Role | Typst (PDF) | HTML/CSS | Rationale |
|------|-------------|----------|-----------|
| Body | `"IBM Plex Sans"` | `"IBM Plex Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` | Humanist sans-serif with excellent readability at small sizes; technical feel without being cold |
| Heading | `"IBM Plex Sans"` (same family, weight varies) | Same stack as body | Single font family keeps the design cohesive |
| Monospace | `"IBM Plex Mono"` | `"IBM Plex Mono", "JetBrains Mono", "Fira Code", "SF Mono", "Cascadia Code", "Consolas", monospace` | Used for skill chips, metadata lines, and inline code |

**Fallback strategy for Typst:** If IBM Plex Sans is not installed, the Typst template falls back to `"Inter"`, then `"Source Sans 3"` (bundled with rendercv's Typst package). The Pydantic model exposes `font_family.body`, `font_family.heading`, and `font_family.mono` as configurable fields.

### Type Scale

All sizes are specified in `pt` for Typst and `rem` for HTML (with `1rem = 10pt` base).

| Element | Typst Size | HTML Size | Weight | Transform | Usage |
|---------|-----------|-----------|--------|-----------|-------|
| Name (h1) | `24pt` | `2.4rem` | 700 (bold) | None | Candidate name, top of page |
| Headline | `11pt` | `1.1rem` | 400 (regular) | None | Role/tagline below name |
| Connections | `9pt` | `0.9rem` | 400 (regular) | None | Email, phone, links in header |
| Section title (h2) | `12pt` | `1.2rem` | 600 (semibold) | Uppercase | "EXPERIENCE", "EDUCATION", etc. |
| Entry title (h3) | `10.5pt` | `1.05rem` | 600 (semibold) | None | Company name, institution, project name |
| Entry subtitle | `10pt` | `1.0rem` | 400 (regular) | Italic | Position title, degree, role |
| Body text | `10pt` | `1.0rem` | 400 (regular) | None | Highlights, descriptions, bullet text |
| Meta text | `9pt` | `0.9rem` | 400 (regular) | None | Dates, locations, GitHub metadata line |
| Skill chip text | `8.5pt` | `0.85rem` | 500 (medium) | None | Text inside skill chips |
| Footer | `8pt` | `0.8rem` | 400 (regular) | None | Page number, last updated |

### Line Spacing

| Context | Line height | Rationale |
|---------|------------|-----------|
| Body text | `1.35` | Comfortable reading density for bullet points |
| Highlights (bullet lists) | `1.3` | Slightly tighter than body for compact lists |
| Entry header block | `1.2` | Tight grouping of title/subtitle/meta |
| Section title | `1.0` | Single line, no extra leading needed |

### Letter Spacing

| Element | Tracking |
|---------|----------|
| Section titles (uppercase) | `+0.08em` | Compensates for uppercase readability loss |
| All other text | `0` (default) | No tracking adjustment |

---

## 3. Color Palette

The palette is intentionally restrained. Two accent colors maximum. Everything else is a gray.

### Light Mode (Default and Only Mode)

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `text-primary` | `#1a1a2e` | `rgb(26, 26, 46)` | Body text, entry titles — near-black with slight warmth |
| `text-secondary` | `#4a4a68` | `rgb(74, 74, 104)` | Subtitles, meta text, dates — softer than primary |
| `text-muted` | `#7a7a94` | `rgb(122, 122, 148)` | Footer, tertiary info — clearly deemphasized |
| `accent-primary` | `#2563eb` | `rgb(37, 99, 235)` | Section title underline, links — "blue-600" in Tailwind terms |
| `accent-hover` | `#1d4ed8` | `rgb(29, 78, 216)` | Link hover state (HTML only) — "blue-700" |
| `chip-bg` | `#f0f4ff` | `rgb(240, 244, 255)` | Skill chip background — very light blue tint |
| `chip-border` | `#dbe4ff` | `rgb(219, 228, 255)` | Skill chip border — slightly darker than chip-bg |
| `chip-text` | `#2563eb` | `rgb(37, 99, 235)` | Skill chip text — matches accent-primary |
| `rule` | `#e2e4ea` | `rgb(226, 228, 234)` | Horizontal rules, section dividers — subtle gray |
| `background` | `#ffffff` | `rgb(255, 255, 255)` | Page background — pure white |
| `meta-icon` | `#7a7a94` | `rgb(122, 122, 148)` | Star icon, separator dots in metadata line |

### Pydantic Model Color Fields

The theme's Pydantic model exposes these as configurable `Color` fields:

```python
class DevforgeColors(BaseModelWithoutExtraKeys):
    body: Color = Color("rgb(26, 26, 46)")
    name: Color = Color("rgb(26, 26, 46)")
    headline: Color = Color("rgb(74, 74, 104)")
    connections: Color = Color("rgb(74, 74, 104)")
    section_titles: Color = Color("rgb(26, 26, 46)")
    accent: Color = Color("rgb(37, 99, 235)")
    links: Color = Color("rgb(37, 99, 235)")
    muted: Color = Color("rgb(122, 122, 148)")
    chip_background: Color = Color("rgb(240, 244, 255)")
    chip_border: Color = Color("rgb(219, 228, 255)")
    chip_text: Color = Color("rgb(37, 99, 235)")
    footer: Color = Color("rgb(122, 122, 148)")
```

---

## 4. Skill Chip Rendering

Skills are rendered as inline "chips" (also called tags or badges) — small rounded rectangles that flow inline like words in a paragraph. This is the signature visual feature of devforge.

### Visual Specification

```
┌─────────────┐  ┌──────┐  ┌────────────┐  ┌───────┐
│  Kubernetes  │  │  Go  │  │  Terraform  │  │  AWS  │
└─────────────┘  └──────┘  └────────────┘  └───────┘
```

| Property | Value |
|----------|-------|
| Background color | `chip-bg` (`#f0f4ff`) |
| Border | `1px solid chip-border` (`#dbe4ff`) |
| Border radius | `4px` (Typst: `3pt`) |
| Text color | `chip-text` (`#2563eb`) |
| Font | Monospace stack at `8.5pt` / `0.85rem`, weight 500 |
| Horizontal padding | `6px` / `4pt` |
| Vertical padding | `2px` / `1.5pt` |
| Gap between chips | `6px` / `4pt` horizontal, `4px` / `3pt` vertical |
| Line wrapping | Chips wrap naturally to the next line like inline text |

### Typst Implementation Approach

In Typst, skill chips are rendered using `box()` with `fill`, `stroke`, `inset`, and `radius`:

```typst
#let skill-chip(content) = box(
  fill: rgb(240, 244, 255),
  stroke: 1pt + rgb(219, 228, 255),
  radius: 3pt,
  inset: (x: 4pt, y: 1.5pt),
  text(8.5pt, weight: 500, font: "IBM Plex Mono", fill: rgb(37, 99, 235), content)
)
```

Skills within a section are rendered as a flowing paragraph of chips separated by `h(4pt)` horizontal space, allowing natural line wrapping.

### HTML Implementation Approach

```css
.skill-chip {
  display: inline-block;
  background: var(--chip-bg);
  border: 1px solid var(--chip-border);
  border-radius: 4px;
  color: var(--chip-text);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 500;
  padding: 2px 6px;
  margin: 0 4px 4px 0;
  white-space: nowrap;
}
```

### When Chips Are Used

Skill chips are used ONLY for `OneLineEntry` items within sections whose title contains "skill" (case-insensitive match). This is detected at template render time. All other entry types render normally. The heuristic:

1. Section title contains "skill" (e.g., "Skills", "Technical Skills", "Core Skills") -- render OneLineEntry items as chips.
2. Otherwise, OneLineEntry renders in its standard format (name + detail on one line).

### ATS Safety

The chip rendering is purely visual. In the ATS HTML output, skills render as a plain comma-separated list within a `<ul>` or `<p>` element. In Markdown output, skills render as a comma-separated list. The chip styling exists only in the Typst/PDF and styled HTML outputs.

---

## 5. Project Metadata Line

Projects sourced from GitHub (via `anvil scan`) include a metadata line that mirrors the GitHub repository page aesthetic.

### Format

```
★ 234 · Go · Updated Mar 2026
```

| Component | Display | Source Field |
|-----------|---------|-------------|
| Star icon | `★` (U+2605) | Literal character |
| Star count | Integer, no separator for <10k; `12.3k` for >=10k | `stars` from GitHub scan data |
| Separator | ` · ` (space-middot-space, U+00B7) | Literal |
| Language | Primary language name | `primary_language` from GitHub data |
| Separator | ` · ` | Literal |
| Updated | `Updated Mon YYYY` (e.g., "Updated Mar 2026") | `last_push` from GitHub data, formatted |

### Visual Styling

| Property | Value |
|----------|-------|
| Font | Monospace stack at `9pt` / `0.9rem` |
| Color | `text-muted` (`#7a7a94`) |
| Star icon color | `text-muted` (same as text for ATS safety — no image icons) |
| Position | Immediately below the project entry title line |
| Spacing above | `2pt` / `2px` |
| Spacing below | `4pt` / `4px` (before highlights/description) |

### Conditional Rendering

The metadata line renders only when at least one of `stars`, `primary_language`, or `last_push` is present in the entry data. Components with missing data are omitted (separators adjust automatically). If none are present, no metadata line renders and the entry appears as a standard NormalEntry.

### Data Source

Metadata values come from the `anvil` extension fields on entries generated by `anvil scan --github`. These are stored in the YAML as part of the entry:

```yaml
projects:
  - name: k8s-autoscaler
    date: "2024-01 to present"
    highlights:
      - "Custom metrics autoscaler for Kubernetes HPA"
    url: https://github.com/janedeveloper/k8s-autoscaler
    # Anvil extension — ignored by rendercv, used by devforge templates:
    # (stored in the anvil.project_metadata section, keyed by entry name)
```

The template checks for metadata availability and renders the line only when data exists. Standard rendercv YAML without metadata produces no metadata line — the project renders as a plain NormalEntry.

---

## 6. Section Header Styling

Section headers use uppercase text with a short accent-colored underline. This is the "partial line" style but with color.

### Visual Specification

```
EXPERIENCE
──────────  (accent-colored line, extends ~30% of content width)

  [entries...]

EDUCATION
─────────

  [entries...]
```

| Property | Value |
|----------|-------|
| Text | Section title, uppercased via `text-transform: uppercase` (CSS) / Typst `upper()` |
| Font | Body font (IBM Plex Sans), `12pt` / `1.2rem`, weight 600 |
| Letter spacing | `+0.08em` (compensates for uppercase) |
| Color | `text-primary` (`#1a1a2e`) |
| Underline color | `accent-primary` (`#2563eb`) |
| Underline thickness | `2pt` / `2px` |
| Underline width | `40pt` (fixed) — short accent stroke, not full-width |
| Underline gap | `4pt` below text baseline |
| Space above section | `14pt` / `14px` (first section: `8pt`) |
| Space below underline | `8pt` / `8px` (before first entry) |

### Typst Implementation Approach

```typst
#let devforge-section-title(title) = {
  v(14pt)
  text(12pt, weight: 600, tracking: 0.08em, upper(title))
  v(4pt)
  line(length: 40pt, stroke: 2pt + rgb(37, 99, 235))
  v(8pt)
}
```

### HTML Implementation Approach

```css
.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-primary);
  margin-top: 14px;
  margin-bottom: 0;
  padding-bottom: 4px;
  border-bottom: 2px solid var(--accent-primary);
  display: inline-block;  /* underline only extends to text width, capped at min 40px */
  min-width: 40px;
}
```

Note: In the HTML version, the underline naturally matches the text width (via `display: inline-block`) rather than using a fixed 40pt. This is acceptable — the visual effect is similar and adapts better to varying section title lengths.

---

## 7. Spacing System

Consistent vertical rhythm based on a `4pt` base unit. All spacing values are multiples of 4pt.

### Vertical Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `space-xs` | `2pt` / `2px` | Metadata line gap, tight inline spacing |
| `space-sm` | `4pt` / `4px` | Between chips, between bullet items |
| `space-md` | `8pt` / `8px` | Below section underline, between entry sub-elements |
| `space-lg` | `12pt` / `12px` | Between entries within a section |
| `space-xl` | `14pt` / `14px` | Above section titles |
| `space-2xl` | `20pt` / `20px` | Below header block (before first section) |

### Spacing Application

| Context | Spacing |
|---------|---------|
| Below candidate name | `space-sm` (`4pt`) |
| Below headline | `space-sm` (`4pt`) |
| Below connections | `space-2xl` (`20pt`) |
| Above section title | `space-xl` (`14pt`) — first section uses `space-md` (`8pt`) |
| Below section underline | `space-md` (`8pt`) |
| Between entries (regular: Experience, Education, Normal, Publication) | `space-lg` (`12pt`) |
| Between entries (text-based: Bullet, Numbered, ReversedNumbered, Text) | `space-sm` (`4pt`) |
| Between entry title line and subtitle line | `space-xs` (`2pt`) |
| Between subtitle/meta and highlights | `space-sm` (`4pt`) |
| Between highlight bullet items | `space-sm` (`4pt`) |
| Between highlight bullet and its text | `6pt` horizontal |

### Pydantic Model Spacing Fields

```python
class DevforgeSpacing(BaseModelWithoutExtraKeys):
    space_above_section_titles: TypstDimension = "14pt"
    space_below_section_titles: TypstDimension = "8pt"
    space_between_regular_entries: TypstDimension = "12pt"
    space_between_text_entries: TypstDimension = "4pt"
    space_below_header: TypstDimension = "20pt"
    highlight_item_spacing: TypstDimension = "4pt"
    highlight_left_margin: TypstDimension = "12pt"
```

---

## 8. Entry Layouts

Each of rendercv's entry types has a defined visual layout in devforge. All layouts are single-column (no date-and-location side column).

### 8.1 ExperienceEntry

Fields: `company`, `position`, `date`, `location`, `highlights`, `url`

```
Company Name                                          Jan 2023 - Present
Position Title                                                Austin, TX
  - Designed and implemented distributed caching layer reducing p99
    latency by 40% across 12 microservices
  - Led migration from monolithic deployment to Kubernetes, serving
    2.3M daily active users with zero downtime
```

| Line | Content | Style |
|------|---------|-------|
| Line 1 (left) | Company name | `10.5pt`, weight 600, `text-primary` |
| Line 1 (right) | Date string | `9pt`, weight 400, `text-secondary`, right-aligned |
| Line 2 (left) | Position | `10pt`, weight 400, italic, `text-secondary` |
| Line 2 (right) | Location | `9pt`, weight 400, `text-secondary`, right-aligned |
| Highlights | Bulleted list | `10pt`, weight 400, `text-primary`, bullet: `•`, left margin `12pt` |

If `url` is present, the company name is a hyperlink styled in `accent-primary` color.

### 8.2 EducationEntry

Fields: `institution`, `area`, `degree`, `date`, `location`, `highlights`, `url`

```
Massachusetts Institute of Technology                 Sep 2018 - Jun 2022
BS in Computer Science                                    Cambridge, MA
  - GPA: 3.9/4.0, Dean's List all semesters
```

| Line | Content | Style |
|------|---------|-------|
| Line 1 (left) | Institution | `10.5pt`, weight 600, `text-primary` |
| Line 1 (right) | Date string | `9pt`, weight 400, `text-secondary` |
| Line 2 (left) | Degree + " in " + Area | `10pt`, weight 400, italic, `text-secondary` |
| Line 2 (right) | Location | `9pt`, weight 400, `text-secondary` |
| Highlights | Bulleted list (same as ExperienceEntry) |

If only `area` is present (no `degree`), line 2 shows just the area. If only `degree` is present, line 2 shows just the degree.

### 8.3 NormalEntry

Fields: `name`, `date`, `location`, `highlights`, `url`

```
k8s-autoscaler                                        2024 - Present
★ 234 · Go · Updated Mar 2026
  - Custom metrics autoscaler for Kubernetes HPA with
    Prometheus integration
```

| Line | Content | Style |
|------|---------|-------|
| Line 1 (left) | Name | `10.5pt`, weight 600, `text-primary` |
| Line 1 (right) | Date string | `9pt`, weight 400, `text-secondary` |
| Metadata line | GitHub metadata (if present) | `9pt`, monospace, `text-muted` |
| Highlights | Bulleted list (same as ExperienceEntry) |

The metadata line is unique to devforge and only appears when GitHub metadata is available (see section 5).

### 8.4 PublicationEntry

Fields: `title`, `authors`, `journal`, `date`, `doi`, `url`

```
Efficient Autoscaling Policies for Stateful Workloads
J. Developer, A. Coauthor, B. Advisor
Journal of Cloud Computing, 2024
```

| Line | Content | Style |
|------|---------|-------|
| Line 1 | Title | `10.5pt`, weight 600, `text-primary` (hyperlinked if URL/DOI present) |
| Line 2 | Authors | `10pt`, weight 400, `text-secondary` |
| Line 3 | Journal + ", " + Date | `9pt`, weight 400, italic, `text-muted` |

### 8.5 OneLineEntry

Fields: `name`, `details`

**Standard rendering (non-skills sections):**

```
AWS Solutions Architect Professional — Issued Jan 2024
```

| Part | Style |
|------|-------|
| Name | `10pt`, weight 600, `text-primary` |
| Separator | ` — ` (em dash) |
| Details | `10pt`, weight 400, `text-secondary` |

**Skill chip rendering (skills sections):**

```
┌─────────────┐  ┌──────┐  ┌────────────┐  ┌───────┐  ┌──────────┐
│  Kubernetes  │  │  Go  │  │  Terraform  │  │  AWS  │  │  Python  │
└─────────────┘  └──────┘  └────────────┘  └───────┘  └──────────┘
```

When the section title matches the skill heuristic (see section 4), the `name` field of each OneLineEntry renders as a chip. The `details` field, if present, renders as a parenthetical after the chip group (e.g., a skill category heading).

### 8.6 BulletEntry

Fields: `bullet` (a single string)

```
  • Led a team of 5 engineers to deliver the project 2 weeks ahead of schedule
```

| Property | Value |
|----------|-------|
| Bullet character | `•` (U+2022) |
| Left margin | `12pt` |
| Bullet-to-text gap | `6pt` |
| Font | Body font, `10pt`, weight 400, `text-primary` |

### 8.7 NumberedEntry

Fields: `bullet` (a single string), rendered with sequential numbering

```
  1. First item in an ordered list
  2. Second item in an ordered list
```

| Property | Value |
|----------|-------|
| Number format | `N.` (arabic numeral + period) |
| Left margin | `12pt` |
| Number-to-text gap | `6pt` |
| Font | Body font, `10pt`, weight 400, `text-primary` |

### 8.8 ReversedNumberedEntry

Same as NumberedEntry but numbered in reverse order (last entry is 1, first is N). Used for publication numbering where most recent is #1.

### 8.9 TextEntry

Fields: `text` (a freeform string)

```
Passionate about building developer tools and infrastructure that
scales. Open source contributor with 500+ commits across 15 repos.
```

| Property | Value |
|----------|-------|
| Font | Body font, `10pt`, weight 400, `text-primary` |
| Alignment | Left-aligned (not justified, to match the clean/modern aesthetic) |
| Max width | Full content width |

---

## 9. Responsive Behavior (HTML Output)

The styled HTML output (not the ATS HTML, which is unstyled) adapts to viewport width using CSS breakpoints. No JavaScript is used.

### Breakpoints

| Name | Width | Behavior |
|------|-------|----------|
| Desktop | `>= 768px` | Full layout with horizontal padding equivalent to page margins |
| Mobile | `< 768px` | Reduced padding, slightly smaller type scale |

### Desktop (>= 768px)

- Content centered with `max-width: 720px` and `margin: 0 auto`
- Full type scale as specified in section 2
- Entry title/date on same line (flexbox row with `justify-content: space-between`)
- Skill chips wrap naturally

### Mobile (< 768px)

- Horizontal padding: `16px` (replaces page margins)
- Name font size: `2.0rem` (down from `2.4rem`)
- Entry title and date stack vertically (date moves below title)
- Entry subtitle and location stack vertically
- All other sizes remain the same (already optimized for small screens)
- Skill chips wrap naturally (no change needed)

### CSS Custom Properties

All colors and key dimensions are exposed as CSS custom properties on `:root` for easy theming:

```css
:root {
  --text-primary: #1a1a2e;
  --text-secondary: #4a4a68;
  --text-muted: #7a7a94;
  --accent-primary: #2563eb;
  --accent-hover: #1d4ed8;
  --chip-bg: #f0f4ff;
  --chip-border: #dbe4ff;
  --chip-text: #2563eb;
  --rule: #e2e4ea;
  --background: #ffffff;
  --font-body: "IBM Plex Sans", "Inter", -apple-system, BlinkMacSystemFont,
               "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: "IBM Plex Mono", "JetBrains Mono", "Fira Code", "SF Mono",
               "Cascadia Code", "Consolas", monospace;
  --content-max-width: 720px;
}
```

### Print Styles

The HTML output includes `@media print` styles that:
- Remove all margins/padding (the browser's print margins take over)
- Force `background: white`, `color: black`
- Render skill chips with visible borders (some browsers strip backgrounds in print)
- Hide any interactive elements (none planned, but defensive)

---

## 10. Typst Specifics (PDF Output)

### Typst Package Dependency

Devforge templates use the same `@preview/rendercv:0.2.0` Typst package as the classic theme. The devforge theme overrides specific rendering functions (section headers, entry layouts, skill chips) while reusing the package's core infrastructure (page setup, header rendering, footer).

### Font Configuration

The Typst preamble sets up fonts:

```typst
#set text(font: "IBM Plex Sans", fallback: true)
```

Typst will automatically fall back through its font resolution if IBM Plex Sans is not available. The Pydantic model allows users to override all three font roles.

### Page Setup

```typst
#set page(
  paper: "us-letter",  // or "a4"
  margin: (top: 0.6in, bottom: 0.6in, left: 0.7in, right: 0.7in),
)
```

### Custom Typst Functions

The devforge theme defines these Typst helper functions (injected via the Jinja2 preamble template):

| Function | Purpose |
|----------|---------|
| `skill-chip(content)` | Renders a single skill chip box |
| `devforge-section-title(title)` | Renders section header with accent underline |
| `meta-line(..components)` | Renders GitHub-style metadata line with `·` separators |
| `entry-header(left-top, right-top, left-bottom, right-bottom)` | Two-line entry header with left/right alignment |
| `highlight-list(..items)` | Renders bulleted highlight list with consistent spacing |

### Template File Structure

```
src/anvilcv/themes/devforge/templates/
├── typst/
│   ├── Preamble.j2.typ          # Page setup, font config, helper functions
│   ├── Header.j2.typ            # Name, headline, connections
│   ├── SectionBeginning.j2.typ  # Section title with accent underline
│   ├── SectionEnding.j2.typ     # Section close (minimal)
│   └── entries/
│       ├── ExperienceEntry.j2.typ
│       ├── EducationEntry.j2.typ
│       ├── NormalEntry.j2.typ
│       ├── PublicationEntry.j2.typ
│       ├── OneLineEntry.j2.typ
│       ├── BulletEntry.j2.typ
│       ├── NumberedEntry.j2.typ
│       ├── ReversedNumberedEntry.j2.typ
│       └── TextEntry.j2.typ
└── markdown/
    ├── Header.j2.md
    ├── SectionBeginning.j2.md
    ├── SectionEnding.j2.md
    └── entries/
        ├── ExperienceEntry.j2.md
        ├── EducationEntry.j2.md
        ├── NormalEntry.j2.md
        ├── PublicationEntry.j2.md
        ├── OneLineEntry.j2.md
        ├── BulletEntry.j2.md
        ├── NumberedEntry.j2.md
        ├── ReversedNumberedEntry.j2.md
        └── TextEntry.j2.md
```

---

## 11. Pydantic Design Model

The devforge theme has its own Pydantic model that participates in rendercv's theme discriminated union (registered in `built_in_design.py`). It does NOT inherit from `ClassicTheme` — it is a standalone model with its own field structure, since devforge's single-column layout is fundamentally different from the classic theme's two-column entry design.

### Model Skeleton

```python
class DevforgeTheme(BaseModelWithoutExtraKeys):
    """Devforge theme: clean, modern, developer-focused resume design."""

    theme: Literal["devforge"] = "devforge"

    # Page
    page: DevforgePage  # size, margins, show_footer

    # Colors
    colors: DevforgeColors  # body, accent, links, chips, muted, etc.

    # Typography
    typography: DevforgeTypography
    #   font_family: DevforgeFontFamily  # body, heading, mono
    #   font_size: DevforgeFontSize      # name, headline, section_title, body, meta
    #   line_spacing: float = 1.35

    # Section titles
    section_titles: DevforgeSectionTitles
    #   type: Literal["accent_underline"] = "accent_underline"
    #   underline_width: TypstDimension = "40pt"
    #   space_above: TypstDimension = "14pt"
    #   space_below: TypstDimension = "8pt"

    # Entries
    entries: DevforgeEntries
    #   space_between_regular: TypstDimension = "12pt"
    #   space_between_text: TypstDimension = "4pt"
    #   highlight_bullet: str = "•"
    #   highlight_left_margin: TypstDimension = "12pt"

    # Skill chips
    skill_chips: DevforgeSkillChips
    #   enabled: bool = True
    #   background: Color
    #   border: Color
    #   text_color: Color
    #   border_radius: TypstDimension = "3pt"
    #   font_size: TypstDimension = "8.5pt"

    # Links
    links: DevforgeLinks
    #   underline: bool = True
    #   color: Color (defaults to accent-primary)

    # Header
    header: DevforgeHeader
    #   alignment: Literal["left", "center"] = "left"
    #   space_below_name: TypstDimension = "4pt"
    #   space_below_headline: TypstDimension = "4pt"
    #   space_below_connections: TypstDimension = "20pt"
    #   connections_separator: str = " · "
```

### User-Facing YAML Configuration

```yaml
design:
  theme: devforge

  # All fields below are optional — defaults produce the standard devforge look.
  page:
    size: us-letter
    top_margin: 0.6in
    bottom_margin: 0.6in
    left_margin: 0.7in
    right_margin: 0.7in

  colors:
    accent: "rgb(37, 99, 235)"  # Change the accent color

  typography:
    font_family:
      body: "IBM Plex Sans"
      mono: "IBM Plex Mono"

  skill_chips:
    enabled: true  # Set to false to render skills as plain text
```

---

## 12. ATS Compatibility Guarantees

Devforge is designed to score well on Anvil's own ATS scorer (F-ANV-04). These constraints are non-negotiable:

| Rule | Guarantee |
|------|-----------|
| Single-column layout | No multi-column regions. Dates are inline, not in a side column. |
| Machine-readable text | All text is in the DOM (HTML) or Typst text nodes (PDF). No text in images. |
| Standard section headers | Section titles use common resume keywords: "Experience", "Education", "Skills", "Projects", "Publications". Custom section names are user-controlled but devforge does not rename them. |
| No tables for layout | HTML uses `<section>`, `<article>`, `<h1>`-`<h3>`, `<ul>`, `<p>`. No `<table>` elements. |
| No CSS-only content | No `::before`/`::after` pseudo-elements for substantive text. Bullets use real list markers or inline characters. |
| Readable link text | Links use descriptive text, not raw URLs. URL is in `href` attribute. |
| Linear reading order | HTML source order matches visual order. No CSS `order`, `position: absolute`, or `float` for layout. |
| Font embedding | Typst PDF output embeds all fonts. No reliance on system fonts for PDF rendering. |

---

## 13. Comparison with Classic Theme

| Aspect | Classic (rendercv) | Devforge (Anvil) |
|--------|-------------------|------------------|
| Layout | Two-column entries (content + date/location column) | Single-column (dates inline with titles) |
| Section headers | Partial line or full line (configurable) | Uppercase + short accent underline |
| Skills | Bulleted list or one-line entries | Inline chips with colored background |
| Project metadata | Not supported | GitHub-style metadata line |
| Font | Source Sans 3 (bundled) | IBM Plex Sans (system, with fallbacks) |
| Color scheme | Blue accent on white | Blue accent on white (similar palette, refined tokens) |
| Entry spacing | Configurable column widths + side space | Simplified: just vertical spacing |
| Pydantic model | ClassicTheme (33KB, 200+ fields) | DevforgeTheme (compact, ~40 fields) |

---

## 14. Implementation Checklist

This checklist tracks the work required to implement the devforge theme. Each item maps to a testable deliverable.

- [ ] **14.1** `DevforgeTheme` Pydantic model with all sub-models (`DevforgePage`, `DevforgeColors`, `DevforgeTypography`, `DevforgeSectionTitles`, `DevforgeEntries`, `DevforgeSkillChips`, `DevforgeLinks`, `DevforgeHeader`)
- [ ] **14.2** Register `DevforgeTheme` in the theme discriminated union (`built_in_design.py`)
- [ ] **14.3** Typst preamble template (`Preamble.j2.typ`) with page setup, font config, and all helper functions
- [ ] **14.4** Typst header template (`Header.j2.typ`)
- [ ] **14.5** Typst section begin/end templates
- [ ] **14.6** Typst entry templates for all 9 entry types (8 unique + ReversedNumbered which reuses Numbered logic)
- [ ] **14.7** Skill chip detection logic (section title heuristic) in the template or model processor
- [ ] **14.8** Project metadata line rendering in NormalEntry template
- [ ] **14.9** Markdown templates for all entry types (used for HTML generation pipeline)
- [ ] **14.10** Styled HTML output with CSS custom properties, responsive breakpoints, and print styles
- [ ] **14.11** Sample devforge YAML file for snapshot testing
- [ ] **14.12** Snapshot tests: render sample YAML, verify Typst output matches golden file
- [ ] **14.13** Verify ATS scorer gives >= 85 score on devforge-rendered output
