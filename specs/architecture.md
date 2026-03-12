# Architecture Overview

## Fork Base

Anvil forks rendercv at tag **v2.7** (released 2026-03-06) using a **vendor + patch file** strategy. The vendored source lives at `src/anvilcv/vendor/rendercv/` to maintain a clear boundary between upstream code and Anvil additions. Each modification to vendored code is tracked as a documented patch in `patches/` (see [Fork Maintenance](fork-maintenance.md) for the full patch index and evaluation process).

## rendercv Module Inventory (v2.7)

Every rendercv module is classified by how Anvil treats it. Build agents MUST consult this inventory before modifying any vendored file.

### Classification Key

- **Untouched** — Used as-is. Do not modify. Safe to cherry-pick upstream changes.
- **Extended** — Anvil adds to it (new subclasses, new registrations) but does not change existing code. Upstream changes are usually safe to merge.
- **Modified** — Anvil changes internals. Upstream changes require manual review and conflict resolution.
- **Wrapped** — Anvil calls it through a thin adapter. The original module is untouched, but Anvil intercepts inputs/outputs.

### Top-Level Files

| Module | Path | Purpose | Anvil Status | Notes |
|--------|------|---------|-------------|-------|
| `__init__.py` | `src/rendercv/__init__.py` | Package init, `__version__` | **Modified** | Anvil changes package name and version |
| `__main__.py` | `src/rendercv/__main__.py` | `python -m rendercv` | **Modified** | Points to Anvil entry point |
| `exception.py` | `src/rendercv/exception.py` | Custom exceptions (RenderCVUserError, RenderCVInternalError) | **Untouched** | Anvil adds new exception classes in separate file |

### `cli/` — Command-Line Interface

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `app.py` | `cli/app.py` | 5KB | Typer app setup, version checking, auto-imports `*_command.py` | **Modified** | Anvil replaces the Typer app; adds new subcommands (score, tailor, scan, prep, cover, deploy). Version check points to anvilcv PyPI. |
| `entry_point.py` | `cli/entry_point.py` | 754B | Entry point for `rendercv` binary | **Modified** | Entry point becomes `anvil` binary |
| `error_handler.py` | `cli/error_handler.py` | 1.5KB | CLI error formatting | **Extended** | Anvil adds error formatting for AI/API failures |
| `copy_templates.py` | `cli/copy_templates.py` | 886B | Copy template files for customization | **Untouched** | |
| `render_command/` | | | The `render` subcommand | | |
| ↳ `render_command.py` | `cli/render_command/render_command.py` | 7.2KB | Typer command definition with flags | **Extended** | Anvil adds `--variant` flag, ATS HTML output option |
| ↳ `run_rendercv.py` | `cli/render_command/run_rendercv.py` | 6.4KB | Pipeline: YAML → Typst → PDF → PNG → MD → HTML | **Extended** | Anvil adds ATS HTML generation step after standard HTML |
| ↳ `progress_panel.py` | `cli/render_command/progress_panel.py` | 6KB | Rich progress display | **Untouched** | |
| ↳ `parse_override_arguments.py` | `cli/render_command/parse_override_arguments.py` | 1.9KB | CLI override arg parsing | **Untouched** | |
| ↳ `watcher.py` | `cli/render_command/watcher.py` | 2.1KB | File watcher for live reload | **Untouched** | |
| `new_command/` | | | The `new` subcommand | **Extended** | Anvil's `new` generates Anvil-flavored YAML with extended fields |
| `create_theme_command/` | | | The `create-theme` subcommand | **Untouched** | |

### `schema/` — Data Models & Validation

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `rendercv_model_builder.py` | `schema/rendercv_model_builder.py` | 7.5KB | Builds RenderCVModel from YAML with overlay support | **Wrapped** | Anvil wraps to build `AnvilModel` (extends RenderCVModel) |
| `json_schema_generator.py` | `schema/json_schema_generator.py` | 1.5KB | Generates JSON Schema for editor autocompletion | **Extended** | Anvil generates extended schema including Anvil fields |
| `pydantic_error_handling.py` | `schema/pydantic_error_handling.py` | 9.6KB | Custom Pydantic error formatting | **Untouched** | |
| `override_dictionary.py` | `schema/override_dictionary.py` | 3.7KB | Dict override/merge logic | **Untouched** | |
| `variant_pydantic_model_generator.py` | `schema/variant_pydantic_model_generator.py` | ~5KB | Dynamic model variant generation | **Untouched** | |
| `sample_generator.py` | `schema/sample_generator.py` | 13.4KB | Generates sample YAML content | **Extended** | Anvil adds Anvil-specific sample content |
| `sample_content.yaml` | `schema/sample_content.yaml` | 7.3KB | Default sample CV content | **Extended** | Anvil adds developer-focused sample content |
| `error_dictionary.yaml` | `schema/error_dictionary.yaml` | 1.3KB | Error message templates | **Extended** | Anvil adds error messages for new fields |

### `schema/models/` — Pydantic Models

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `base.py` | `schema/models/base.py` | 278B | `BaseModelWithoutExtraKeys` | **Untouched** | Anvil models inherit from this |
| `rendercv_model.py` | `schema/models/rendercv_model.py` | 2.1KB | Root model: `RenderCVModel(cv, design, locale, settings)` | **Extended** | Anvil subclasses as `AnvilModel` adding `anvil` config section |
| `path.py` | `schema/models/path.py` | 2.6KB | Path resolution for relative paths | **Untouched** | |
| `validation_context.py` | `schema/models/validation_context.py` | 1.9KB | Validation context with input file path | **Untouched** | |
| `custom_error_types.py` | `schema/models/custom_error_types.py` | 160B | Custom Pydantic error types | **Untouched** | |

### `schema/models/cv/` — CV Content Models

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `cv.py` | `schema/models/cv/cv.py` | 9.1KB | Main Cv model (name, headline, location, email, phone, website, social_networks, sections) | **Untouched** | Anvil does NOT modify the Cv model. Extended fields live in the separate `anvil` section. |
| `section.py` | `schema/models/cv/section.py` | 11.9KB | Section model with entry type auto-detection | **Untouched** | |
| `social_network.py` | `schema/models/cv/social_network.py` | 7.4KB | Social network models (GitHub, LinkedIn, etc.) | **Untouched** | |
| `custom_connection.py` | `schema/models/cv/custom_connection.py` | 195B | Custom header connections | **Untouched** | |
| `entries/` | | | Entry type models | | |
| ↳ `bases/` | | | Base entry classes (date handling, common fields) | **Untouched** | |
| ↳ `bullet.py` | | 204B | Bullet (simple string) entry | **Untouched** | |
| ↳ `education.py` | | 778B | Education entry (institution, area, degree, dates) | **Untouched** | |
| ↳ `experience.py` | | 572B | Experience entry (company, position, dates, highlights) | **Untouched** | |
| ↳ `normal.py` | | 412B | Normal entry (name, details) | **Untouched** | |
| ↳ `numbered.py` | | 205B | Numbered entry | **Untouched** | |
| ↳ `one_line.py` | | ~300B | One-line entry (name + details on one line) | **Untouched** | |
| ↳ `publication.py` | | ~800B | Publication entry (title, authors, journal, date) | **Untouched** | |
| ↳ `text.py` | | ~200B | Text (freeform paragraph) entry | **Untouched** | |

### `schema/models/design/` — Theme & Design Models

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `design.py` | `schema/models/design/design.py` | 5.7KB | Main Design model with theme selection | **Extended** | Anvil registers new themes in the theme discriminator |
| `built_in_design.py` | `schema/models/design/built_in_design.py` | 1.7KB | Base class for built-in theme designs | **Untouched** | Anvil themes inherit from this |
| `classic_theme.py` | `schema/models/design/classic_theme.py` | 33KB | Classic theme model (detailed page/color/typography config) | **Untouched** | |
| `color.py` | `schema/models/design/color.py` | 448B | Color type | **Untouched** | |
| `font_family.py` | `schema/models/design/font_family.py` | 672B | Font family type | **Untouched** | |
| `other_themes/` | | | moderncv, sb2nov, engineeringresumes, engineeringclassic | **Untouched** | |

### `schema/models/locale/` — Locale/i18n Models

| Module | Path | Purpose | Anvil Status | Notes |
|--------|------|---------|-------------|-------|
| `locale.py` | `schema/models/locale/locale.py` | Locale model (language, date formats, section name translations) | **Untouched** | Anvil preserves all locale functionality |

### `schema/models/settings/` — Settings Models

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `settings.py` | `schema/models/settings/settings.py` | 2.9KB | Main Settings model | **Untouched** | |
| `render_command.py` | `schema/models/settings/render_command.py` | 5.1KB | Render command settings (output dir, flags) | **Untouched** | |

### `renderer/` — Template Rendering & Output

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `typst.py` | `renderer/typst.py` | 1.1KB | Generates Typst source via Jinja2 → writes `.typ` file | **Untouched** | |
| `pdf_png.py` | `renderer/pdf_png.py` | 4.9KB | Renders PDF from Typst, generates PNG from PDF | **Untouched** | |
| `markdown.py` | `renderer/markdown.py` | 1KB | Generates Markdown via Jinja2 | **Untouched** | |
| `html.py` | `renderer/html.py` | 1.2KB | Generates HTML from Markdown | **Extended** | Anvil adds ATS-optimized HTML generation path |
| `path_resolver.py` | `renderer/path_resolver.py` | 4.1KB | Resolves output file paths | **Extended** | Anvil adds variant-aware path resolution |

### `renderer/templater/` — Jinja2 Template Engine

| Module | Path | Size | Purpose | Anvil Status | Notes |
|--------|------|------|---------|-------------|-------|
| `templater.py` | `renderer/templater/templater.py` | 7.1KB | Main template rendering (render_full_template, render_single_template, render_html) | **Extended** | Anvil adds `render_ats_html` function |
| `model_processor.py` | `renderer/templater/model_processor.py` | 6.9KB | Pre-processes model for templates | **Untouched** | |
| `entry_templates_from_input.py` | `renderer/templater/entry_templates_from_input.py` | 14.3KB | Resolves entry types to template names | **Untouched** | |
| `connections.py` | `renderer/templater/connections.py` | 8.4KB | Connection rendering (social links, email, phone) | **Untouched** | |
| `date.py` | `renderer/templater/date.py` | 9.9KB | Date formatting | **Untouched** | |
| `string_processor.py` | `renderer/templater/string_processor.py` | 4.5KB | String utilities (clean_url) | **Untouched** | |
| `markdown_parser.py` | `renderer/templater/markdown_parser.py` | 5.7KB | Markdown to HTML conversion | **Untouched** | |
| `templates/` | | | Jinja2 template files (per theme, per format) | **Extended** | Anvil adds templates for new themes and ATS HTML |

## Interface Stability Assessment

### Stable Interfaces (safe to depend on)

These rendercv interfaces are well-defined, stable across minor versions, and safe for Anvil to depend on:

- **`RenderCVModel` structure** — The 4-field root model (cv, design, locale, settings) has been stable since v1.x
- **Entry type models** — `EducationEntry`, `ExperienceEntry`, `NormalEntry`, `BulletEntry`, etc. — field names and validation rules are stable
- **`BaseModelWithoutExtraKeys`** — The base class pattern
- **`generate_typst()`, `generate_pdf()`, `generate_png()`, `generate_markdown()`, `generate_html()`** — The renderer function signatures
- **Jinja2 template variable interface** — Templates receive `cv`, `design`, `locale`, `settings` context variables
- **CLI command auto-discovery pattern** — `*_command.py` files auto-registered

### Unstable Interfaces (likely to change upstream)

These may change between rendercv releases and require careful tracking:

- **Theme model internals** — `classic_theme.py` at 33KB has many configurable fields that may be refactored
- **`rendercv_model_builder.py`** — Build logic for overlays and overrides; complex, likely to evolve
- **`variant_pydantic_model_generator.py`** — Dynamic model generation; implementation details may change
- **`sample_generator.py`** — Sample content generation; frequently updated
- **Template file contents** — Jinja2 templates change with theme refinements
- **`pydantic_error_handling.py`** — Error formatting may be restructured

## Import Path Convention

**Build agents: follow these rules for all imports.**

```python
# CORRECT — Anvil's own code:
from anvilcv.ai.provider import AIProvider
from anvilcv.scoring.ats_scorer import ATSScorer

# CORRECT — Vendored rendercv code (accessed through Anvil's namespace):
from anvilcv.vendor.rendercv.schema.models.rendercv_model import RenderCVModel
from anvilcv.vendor.rendercv.renderer.typst import generate_typst

# WRONG — Do not import from rendercv directly:
# from rendercv.schema.models.rendercv_model import RenderCVModel  # ← NEVER DO THIS
```

New Anvil modules should import vendored rendercv code through `anvilcv.vendor.rendercv`, not from `rendercv` directly. This ensures the fork's modifications are picked up and avoids conflicts if the user also has `rendercv` installed.

## Anvil Architecture — New Modules

All new Anvil code lives outside the vendor tree at `src/anvilcv/`:

```
src/anvilcv/
├── __init__.py              # Package init
├── __main__.py              # python -m anvilcv
├── vendor/
│   └── rendercv/            # Vendored rendercv v2.7 (with modifications noted above)
├── cli/
│   ├── app.py               # Anvil CLI app (extends rendercv CLI)
│   ├── entry_point.py       # `anvil` binary entry point
│   ├── score_command/        # `anvil score` — ATS heuristic checker
│   ├── tailor_command/       # `anvil tailor` — AI job tailoring
│   ├── scan_command/         # `anvil scan` — GitHub content generation
│   ├── prep_command/         # `anvil prep` — Interview preparation
│   ├── cover_command/        # `anvil cover` — Cover letter generation
│   ├── deploy_command/       # `anvil deploy` — Web deployment
│   └── watch_command/        # `anvil watch` — Living resume monitor
├── schema/
│   ├── anvil_model.py        # AnvilModel (extends RenderCVModel)
│   ├── anvil_config.py       # Anvil-specific YAML config section
│   ├── job_description.py    # Job description data model
│   ├── variant.py            # Variant tracking model
│   ├── github_profile.py     # GitHub scan data model
│   └── score_report.py       # ATS score report model
├── ai/
│   ├── provider.py           # Provider interface (abstract base)
│   ├── anthropic.py          # Anthropic Claude provider
│   ├── openai.py             # OpenAI provider
│   ├── ollama.py             # Ollama local model provider
│   ├── prompt_registry.py    # Per-provider prompt templates
│   ├── token_budget.py       # Token budget management
│   └── output_parser.py      # Response parsing and validation
├── scoring/
│   ├── ats_scorer.py         # ATS heuristic scoring engine
│   ├── keyword_extractor.py  # Keyword extraction from job descriptions
│   ├── section_detector.py   # Resume section detection
│   ├── parsability_checker.py # Structure and parsability checks
│   └── rules/                # Individual scoring rules with evidence citations
├── github/
│   ├── scanner.py            # GitHub API client and repo crawler. Uses conditional requests (If-None-Match/ETag) to minimize API usage on re-scans. Default --max-repos 100.
│   ├── cache.py              # Aggressive caching in .anvil/github/ with TTL. Conditional requests return 304 Not Modified when data hasn't changed.
│   ├── metrics.py            # Metric extraction (languages, tests, commits)
│   └── entry_generator.py    # Convert GitHub data to resume entries
├── tailoring/
│   ├── job_parser.py         # Job description input: URL (best-effort heuristic parsing via `readability-lxml`), local file, or stdin. URL parsing is best-effort — fails gracefully with suggestion to use file/stdin fallback.
│   ├── matcher.py            # Match resume content to job requirements
│   ├── rewriter.py           # AI bullet rewriting
│   └── variant_writer.py     # Write tailored variant YAML
├── themes/
│   └── devforge/             # Developer-focused theme (v1)
│       ├── __init__.py
│       ├── theme.py          # Pydantic theme model
│       └── templates/        # Jinja2 templates (Typst, Markdown)
│   # terminal/ — Post-v1. Deferred.
├── renderer/
│   ├── ats_html.py           # ATS-optimized semantic HTML renderer
│   └── web_deploy.py         # Vercel deployment — deploys a **static HTML** site: responsive HTML resume + downloadable PDF + minimal CSS (no JS required) + SEO meta tags (og:title, og:description)
└── utils/
    ├── config.py             # API key and configuration management
    └── cache.py              # Caching for GitHub data, LLM responses
```

## Dependency Graph

```
CLI Commands
  ├── render  → schema (RenderCVModel) → renderer (Typst/PDF/HTML/MD/PNG)
  ├── score   → scoring (ATS heuristics) → renderer (for parsing rendered output)
  ├── tailor  → ai (provider abstraction) → tailoring (matcher/rewriter) → schema (variant YAML)
  ├── scan    → github (API client + conditional requests + cache) → schema (GitHub profile → entry generation)
  ├── prep    → ai (provider abstraction) → tailoring (matcher) → schema (job description)
  ├── cover   → ai (provider abstraction) → schema (job description + CV data)
  ├── watch   → github (API polling) → utils (notifications)
  └── deploy  → renderer (HTML) → utils (Vercel API)
```

## Where AI Calls Happen

AI provider calls are isolated to these operations:

1. **`anvil tailor`** — Bullet rewriting, project reordering rationale
2. **`anvil prep`** — Talking point generation
3. **`anvil cover`** — Cover letter text generation
4. **`anvil score`** (optional) — Enhanced keyword extraction from job descriptions (falls back to heuristic extraction without AI)

AI calls never happen during:
- `anvil render` — Pure deterministic rendering
- `anvil new` — Template generation
- `anvil scan` — GitHub API only (no LLM)
- Schema validation — Always deterministic

## Before Writing Code — Build Agent Checklist

Build agents MUST follow this checklist before implementing any task:

1. **Check the module inventory** above. Is the file you're about to create or modify listed? If it's listed as **Untouched**, do NOT modify it. Find another way (extension, wrapper, or new file).
2. **Check for existing functionality.** Search the vendored rendercv code for the function you need before writing a new one. rendercv already has YAML parsing, Pydantic validation, Jinja2 templating, Typst rendering, Markdown generation, HTML generation, CLI arg handling, and watch mode.
3. **Use the correct import path.** Import vendored code via `anvilcv.vendor.rendercv`, not `rendercv`.
4. **New files go in `src/anvilcv/`**, not in the vendor tree. The only exceptions are files listed as **Modified** or **Extended** in the inventory.
5. **If you need to modify a vendored file**, add an entry to `patches/README.md` documenting the change.

## Render Pipeline (Extended)

```
User YAML ──→ AnvilModel validation
                │
                ├── Standard path (unchanged from rendercv):
                │   Model → Jinja2 templates → Typst source → PDF → PNG
                │   Model → Jinja2 templates → Markdown → HTML
                │
                └── Anvil additions:
                    Model → ATS HTML templates → Semantic HTML (section/article/h1-h3)
                    Model → Variant writer → Tailored YAML (new file)
                    Rendered output → ATS scorer → Score report
```
