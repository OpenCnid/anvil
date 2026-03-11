# Implementation Plan

Status: **Phase 0 complete. Phase 1 complete. Phase 2 in progress.** Foundation in place: vendor import hook (find_spec API for Python 3.12+), 4 Modified vendored files patched, CLI scaffold with all 11 commands registered, exceptions, config, cache utilities. AI provider abstraction (F-ANV-09) complete. Extended YAML schema (F-ANV-02) complete. ATS score checker (F-ANV-04, F-ANV-05) complete with keyword matching. Export command (F-ANV-17) complete. AI tailoring pipeline (F-ANV-10) complete. JSON Schema generation (F-ANV-16) complete. Multi-variant rendering (F-ANV-08) complete. GitHub scanner (F-ANV-11) complete. ATS HTML renderer (F-ANV-06) implemented (pipeline integration pending). Interview prep (F-ANV-12) complete. Cover letter (F-ANV-13) complete. Compatibility corpus with 66 integration tests (F-ANV-01). Fork integrity tests in place. 511 tests passing.

**Vendored file key:** Tasks annotate which vendored files they touch.
- `[Modified]` = change internals of vendored file (4 files total)
- `[Extended]` = add to vendored file (13 files total)
- `[Wrapped]` = use through adapter in new file (1 file)
- All other vendored files are **Untouched** — do NOT modify them.

---

## Phase 0: Foundation (Pre-Feature Infrastructure)

These tasks are prerequisites for all features and must be completed first.

- [x] **0.1 Vendor patches: Modified files** — Apply the 4 `[Modified]` patches per `specs/architecture.md`:
  - `src/anvilcv/vendor/rendercv/__init__.py` `[Modified]` — Change package name to `anvilcv`, update version
  - `src/anvilcv/vendor/rendercv/__main__.py` `[Modified]` — Point to Anvil entry point (`anvilcv.__main__`)
  - `src/anvilcv/vendor/rendercv/cli/entry_point.py` `[Modified]` — Rewire to Anvil CLI app
  - `src/anvilcv/vendor/rendercv/cli/app.py` `[Modified]` — Replace Typer app with Anvil's; add new subcommands; version check points to `anvilcv` on PyPI
  - Document each patch in `patches/README.md` with file, purpose, and risk level
- [x] **0.2 Initialize `src/anvilcv/__init__.py`** — Set `__version__`, `__package_name__` ("anvilcv"); this is the Anvil package root (NOT the vendored `__init__.py`)
- [x] **0.3 Create `src/anvilcv/__main__.py`** — Enable `python -m anvilcv`; delegates to `anvilcv.cli.entry_point:main`
- [x] **0.4 Create `src/anvilcv/cli/entry_point.py`** — The `anvil` binary entry point (defined in pyproject.toml as `anvilcv.cli.entry_point:main`); mirrors rendercv's dependency-safe pattern with helpful error on missing deps
- [x] **0.5 Create `src/anvilcv/utils/config.py`** — API key lookup from env vars, `.anvil/config.yaml` loading, provider config resolution
- [x] **0.6 Create `src/anvilcv/utils/cache.py`** — Generic caching utilities for `.anvil/` directory management (used by GitHub scanner, job parser, debug logs)
- [x] **0.7 Error handling foundation** — Define Anvil-specific exception classes (exit codes 1-4 per `specs/cli-interface.md`) in `src/anvilcv/exceptions.py`; integrate with vendored `error_handler.py` `[Extended]`
- [x] **0.8 Test infrastructure** — Create `tests/conftest.py` with shared fixtures (tmp dirs, sample YAML, mock providers); verify `pytest`, `ruff`, `mypy` pass on empty project; create a minimal compatibility corpus fixture (at least 1 rendercv YAML file from rendercv examples)

---

## Phase 1: P0 Features — Launch Blockers

### F-ANV-03: CLI Scaffold (no dependencies)

- [x] **1.1 Create `src/anvilcv/cli/app.py`** — Anvil Typer app with global `--version` and `--help`; register subcommands: `render`, `new`, `score`, `tailor`, `scan`, `prep`, `cover`, `watch`, `deploy`, `export`
- [x] **1.2 Wire render command** — `anvil render` delegates to vendored `rendercv` render pipeline via `anvilcv.vendor.rendercv.cli.render_command`; verify identical behavior to `rendercv render`
- [x] **1.3 Wire new command** — `anvil new` delegates to vendored `new_command` with Anvil extensions (`--theme devforge`, `--rendercv-compat` flag to output pure rendercv YAML without `anvil` section)
- [x] **1.4 Stub remaining subcommands** — Each subcommand (`score`, `tailor`, `scan`, `prep`, `cover`, `watch`, `deploy`, `export`) prints "Not yet implemented" with exit code 0; ensures `anvil --help` lists all commands and each has `--help`
- [x] **1.5 Tests for CLI scaffold** — Test `--help` output, `--version`, exit codes, and that `render` delegates correctly; add to `tests/unit/cli/test_cli.py`

### F-ANV-01: Forward-Compatible Rendering (no dependencies)

- [x] **1.6 Verify vendored render pipeline** — Verified `anvil render` produces Typst, PDF, PNG, Markdown, HTML for valid input; pipeline works correctly through vendored import hook
- [x] **1.7 Build compatibility corpus** — 7 YAML files in `tests/corpus/` covering all 5 themes (classic, sb2nov, engineeringresumes, moderncv, engineeringclassic), all entry types, edge cases (minimal, full)
- [x] **1.8 Compatibility corpus tests** — 66 parametrized tests validating model parsing, Typst generation, Markdown generation, and HTML generation for all corpus files; `tests/integration/rendering/test_compatibility.py`
- [x] **1.9 Fork integrity CI check** — Script that compares all "Untouched" vendored files in `src/anvilcv/vendor/rendercv/` against `baseline/rendercv-v2.7/`; any diff fails the check; place in `tests/integration/test_fork_integrity.py`

### F-ANV-09: AI Provider Abstraction (no dependencies — can parallel with F-ANV-03, F-ANV-01)

- [x] **1.10 Provider interface** — Create `src/anvilcv/ai/provider.py` with abstract base class: `AIProvider`, `ProviderCapabilities`, `GenerationRequest`, `GenerationResponse` dataclasses per `specs/ai-provider-abstraction.md`; include `is_configured()` and `get_setup_instructions()` methods
- [x] **1.11 Anthropic provider** — Create `src/anvilcv/ai/anthropic.py` implementing `AIProvider`; XML-structured prompts; separate system message; claude-sonnet-4-20250514 default; tier-dependent rate limits
- [x] **1.12 OpenAI provider** — Create `src/anvilcv/ai/openai.py`; native JSON mode; separate system message; gpt-4o default
- [x] **1.13 Ollama provider** — Create `src/anvilcv/ai/ollama.py`; llama3.1:8b/70b tested set; others accepted with warning; smaller context window (8K for small models); no auth; local only
- [x] **1.14 Token budget calculator** — Create `src/anvilcv/ai/token_budget.py` per spec: allocate system overhead + few-shot examples + output reserve; truncate job description before resume; explicit error if resume alone exceeds budget
- [x] **1.15 Output parser** — Create `src/anvilcv/ai/output_parser.py` — validate AI responses against expected schema; retry logic (1-3 times with same prompt); save raw failures to `.anvil/debug/` for debugging
- [x] **1.16 Prompt registry skeleton** — Create `src/anvilcv/ai/prompts/` directory structure with task subdirs (`tailor_bullets/`, `cover_letter/`, `interview_prep/`, `keyword_extraction/`); each task dir contains per-provider prompt files (`anthropic.py`, `openai.py`, `ollama.py`)
- [x] **1.17 Provider tests** — Unit tests with mocked API responses for all 3 providers; test error handling (missing key, rate limit, malformed response, network failure, context overflow); `tests/unit/ai/test_providers.py`

### F-ANV-02: Extended YAML Schema (depends on F-ANV-01)

- [x] **1.18 AnvilModel** — Create `src/anvilcv/schema/anvil_model.py` extending `RenderCVModel` with optional `anvil` field; subclass from `anvilcv.vendor.rendercv.schema.models.rendercv_model.RenderCVModel`; the `anvil` field is an `AnvilConfig` Pydantic model
- [x] **1.19 AnvilConfig model** — Create `src/anvilcv/schema/anvil_config.py` with Pydantic models for `providers`, `github`, `variants`, `deploy` sections per `specs/data-model.md`
- [x] **1.20 Job description model** — Create `src/anvilcv/schema/job_description.py` with `JobDescription` Pydantic model (title, company, URL, requirements list, raw_text)
- [x] **1.21 Variant model** — Create `src/anvilcv/schema/variant.py` with provenance metadata (source, job, created_at, provider, model, changes list)
- [x] **1.22 GitHub profile model** — Create `src/anvilcv/schema/github_profile.py` with repo metadata (name, description, url, stars, forks, languages, topics, commits, has_tests, has_ci, license)
- [x] **1.23 Score report model** — Create `src/anvilcv/schema/score_report.py` with overall_score (0-100), parsability, structure, keyword_match sections, recommendations list
- [x] **1.24 Model builder wrapper** — Create `src/anvilcv/schema/model_builder.py` — adapter that wraps vendored `rendercv_model_builder.py` `[Wrapped]` to build `AnvilModel` from YAML; parses and validates the `anvil` section; passes everything else through to vendored builder unchanged
- [x] **1.25 Schema validation tests** — Test that rendercv YAML without `anvil` validates identically to rendercv; test `anvil` section validation; test unknown field rejection; test clear error messages; `tests/unit/schema/test_schema.py`

### F-ANV-04: ATS Score Checker (depends on F-ANV-01)

- [x] **1.26 Text extraction** — Create `src/anvilcv/scoring/text_extractor.py` — extract text from PDF (via `pdfminer.six`, MIT, pure Python) and HTML; preserve position data (x, y, width, height) for layout analysis
- [x] **1.27 Section detector** — Create `src/anvilcv/scoring/section_detector.py` — detect resume sections (Experience, Education, Skills, Projects, Summary, etc.) from extracted text using header pattern matching
- [x] **1.28 Parsability checker** — Create `src/anvilcv/scoring/parsability_checker.py` — implement rules P-01 through P-08 per `specs/ats-scoring-model.md`; each rule returns score + confidence level (evidence-based vs. opinionated heuristic) + evidence
- [x] **1.29 Structure checker** — Create `src/anvilcv/scoring/structure_checker.py` — implement rules S-01 through S-08
- [x] **1.30 ATS scorer engine** — Create `src/anvilcv/scoring/ats_scorer.py` — orchestrates text extraction → section detection → parsability → structure → score calculation; weighted formula: without JD = parsability×0.55 + structure×0.45; with JD = parsability×0.40 + structure×0.30 + keywords×0.30
- [x] **1.31 Score CLI command** — Create `src/anvilcv/cli/score_command/` — implement `anvil score INPUT` with `--format` (text/json), `--output`, `--verbose` options; terminal output with Rich formatting (green ≥80, yellow ≥60, red <60 per spec)
- [x] **1.32 Scoring tests** — Unit tests for each scoring rule (P-01 through P-08, S-01 through S-08) with known-good and known-bad inputs; test score calculation formula; 100% rule coverage required per `specs/success-criteria.md`; `tests/unit/scoring/test_scoring.py`

### F-ANV-05: ATS Score with Job Description (depends on F-ANV-04)

- [x] **1.33 Skills taxonomy** — Create `src/anvilcv/scoring/skills_taxonomy.yaml` with ~500 technical skills and aliases per `specs/ats-scoring-model.md`; categorized by domain (languages, frameworks, cloud, databases, tools, methodologies)
- [x] **1.34 Keyword extractor** — Create `src/anvilcv/scoring/keyword_extractor.py` — heuristic pipeline: section detection → skill extraction (against taxonomy) → requirement parsing (required vs. preferred) → deduplication; optional AI-enhanced extraction when provider configured
- [x] **1.35 Job parser** — Create `src/anvilcv/tailoring/job_parser.py` — multi-source input: URL (via `readability-lxml`), local file, stdin (`--job -`); best-effort URL parsing with graceful fallback; warn on SPA-heavy sites
- [x] **1.36 Keyword match scoring** — Implement rules K-01 through K-05 in `src/anvilcv/scoring/keyword_matcher.py`; integrate with `ats_scorer.py` to enable the 3-category weighted formula
- [x] **1.37 Score + JD CLI integration** — Add `--job` flag to `anvil score`; handle URL fetch errors, partial extraction, SPA warnings per spec error table in `specs/cli-interface.md`
- [x] **1.38 Keyword extraction tests** — Test taxonomy matching, alias deduplication, requirement parsing, section detection; test against sample job descriptions; `tests/unit/scoring/test_keyword_extraction.py`

---

## Phase 2: P1 Features — v1 Must-Haves

### F-ANV-06: ATS-First HTML Output (depends on F-ANV-01)

- [x] **2.1 ATS HTML renderer** — Create `src/anvilcv/renderer/ats_html.py` — semantic HTML with `<section>`, `<article>`, `<h1>`-`<h3>`; all text in DOM (no images-of-text); W3C-valid; CSS for visual styling only
- [ ] **2.2 Extend render pipeline** — Patch vendored `run_rendercv.py` `[Extended]` to add ATS HTML generation step; `_ats.html` output alongside standard outputs; patch vendored `templater.py` `[Extended]` to add `render_ats_html` function
- [ ] **2.3 `--no-ats-html` flag** — Add flag to render command (patch `render_command.py` `[Extended]`) to skip ATS HTML generation
- [x] **2.4 ATS HTML tests** — Validate semantic element usage, text extractability, HTML escaping, file generation; `tests/unit/rendering/test_ats_html.py`

### F-ANV-07: Modern Engineer Theme — devforge (depends on F-ANV-01)

- [ ] **2.5 Author devforge design spec** — Create `specs/devforge-theme.md` with detailed visual design: layout grid, typography (font family, sizes, weights), color palette, skill chip rendering, project metadata line (★ stars · language · updated), section header styling, spacing system, responsive behavior for HTML output. **This MUST precede implementation** per feature tracker success criteria.
- [ ] **2.6 DevForge Pydantic model** — Create `src/anvilcv/themes/devforge/theme.py` — unique design model inheriting from vendored `BuiltInDesign` (`anvilcv.vendor.rendercv.schema.models.design.built_in_design`); configure colors, fonts, spacing, skill chips, project metadata
- [ ] **2.7 DevForge Typst templates** — Create Jinja2 `.j2.typ` templates in `src/anvilcv/themes/devforge/templates/typst/` for ALL entry types: education, experience, normal, bullet, numbered, reversed_numbered, one_line, publication, text
- [ ] **2.8 DevForge Markdown templates** — Create `.j2.md` templates in `src/anvilcv/themes/devforge/templates/markdown/` for all entry types
- [ ] **2.9 DevForge HTML template** — Create `Full.html` template in `src/anvilcv/themes/devforge/templates/html/`
- [ ] **2.10 Register devforge theme** — Patch vendored `design.py` `[Extended]` to register devforge in the theme discriminator alongside existing themes (classic, moderncv, sb2nov, engineeringresumes, engineeringclassic)
- [ ] **2.11 DevForge theme tests** — Render sample CV with devforge; snapshot tests for Typst, Markdown, HTML output; verify ALL entry types render correctly; `tests/unit/test_devforge_theme.py`

### F-ANV-16: JSON Schema Generation (depends on F-ANV-02)

- [x] **2.12 Extended JSON Schema** — Create `src/anvilcv/schema/json_schema.py` generating schema from AnvilModel (includes Anvil-specific fields); Draft-07 compliant; VS Code YAML extension compatible
- [x] **2.13 JSON Schema tests** — Validate schema covers all Anvil fields (anvil config, variant, providers, GitHub); test file generation; `tests/unit/schema/test_json_schema.py`

### F-ANV-17: rendercv Export (depends on F-ANV-02)

- [x] **2.14 Export command** — Create `src/anvilcv/cli/export_command/` — `anvil export INPUT --rendercv --output PATH`; strips `anvil` section from YAML; preserves all other sections byte-identical; uses `ruamel.yaml` to preserve formatting and comments
- [x] **2.15 Export tests** — Test round-trip: Anvil YAML → export → validate with rendercv schema; verify no data loss; `tests/unit/test_export.py`

### F-ANV-08: Multi-Variant Rendering (depends on F-ANV-02)

- [x] **2.16 Variant rendering** — Create `src/anvilcv/rendering/variant_renderer.py` with discovery, path resolution, metadata reading, and batch rendering; variant-specific output subfolders
- [x] **2.17 Variant-aware path resolution** — `get_variant_output_folder()` computes per-variant output paths from variant file stems
- [x] **2.18 Variant rendering tests** — Test discovery, path resolution, metadata reading, empty/missing dirs; `tests/unit/rendering/test_variant_rendering.py`

### F-ANV-10: AI Job Tailoring (depends on F-ANV-02, F-ANV-09)

- [x] **2.19 Matcher** — Create `src/anvilcv/tailoring/matcher.py` — match resume content to job requirements; identify relevant bullets, projects, skills
- [x] **2.20 Rewriter** — Create `src/anvilcv/tailoring/rewriter.py` — AI bullet rewriting using provider interface; per-provider prompts in `src/anvilcv/ai/prompts/tailor_bullets/`
- [x] **2.21 Variant writer** — Create `src/anvilcv/tailoring/variant_writer.py` — write tailored YAML with provenance metadata to `variants/` dir; NEVER modify the user's original file (P1 principle: YAML is source of truth)
- [x] **2.22 Tailor command** — Create `src/anvilcv/cli/tailor_command/` — `anvil tailor INPUT --job <path-or-url> [--provider] [--model] [--render] [--score] [--dry-run]`
- [x] **2.23 Tailor prompts** — Write per-provider prompts for `tailor_bullets` task: `anthropic.py` (XML-tagged output), `openai.py` (JSON mode), `ollama.py` (markdown with extraction)
- [x] **2.24 Tailor tests** — Tier 1 structural tests (output parses as YAML, conforms to AnvilModel schema, provenance metadata present) with mocked APIs; `tests/unit/tailoring/test_tailoring.py`

### F-ANV-11: GitHub Content Scanner (depends on F-ANV-02)

- [x] **2.25 GitHub API client** — Create `src/anvilcv/github/scanner.py` — fetch repos via GitHub REST API with `httpx`; conditional requests (ETag/If-None-Match); `--max-repos 100` default; rate limit awareness (log remaining, pause at 10%)
- [x] **2.26 GitHub cache** — Create `src/anvilcv/github/cache.py` — aggressive caching in `.anvil/github/` with TTL; conditional requests returning 304 use cached data; invalidation on `--force-refresh`
- [x] **2.27 Metrics extractor** — Create `src/anvilcv/github/metrics.py` — extract languages, commits, stars, forks, topics, CI detection (`.github/workflows/`), test detection, license
- [x] **2.28 Entry generator** — Create `src/anvilcv/github/entry_generator.py` — convert GitHub data to rendercv entry YAML (`NormalEntry` format with project metadata line: ★ stars · language · updated)
- [x] **2.29 Scan command** — Create `src/anvilcv/cli/scan_command/` — `anvil scan --github <user> [--merge INPUT] [--max-repos N] [--since DATE]`
- [x] **2.30 Scan tests** — Mock GitHub API responses; test caching, conditional requests, rate limiting, entry generation, CLI; `tests/unit/github/test_scanner.py`

---

## Phase 3: P2 Features — Nice-to-Have

### F-ANV-12: Interview Prep (depends on F-ANV-09, F-ANV-10)

- [x] **3.1 Prep generator** — Create logic to generate per-project talking points matched to job requirements; Markdown output
- [x] **3.2 Prep prompts** — Write prompts for `interview_prep` task in `src/anvilcv/ai/prompts/interview_prep/`
- [x] **3.3 Prep command** — Create `src/anvilcv/cli/prep_command/` — `anvil prep INPUT --job <path-or-url> [--provider] [--output]`
- [x] **3.4 Prep tests** — Tier 1 structural tests with mocked APIs; `tests/unit/test_prep.py`

### F-ANV-13: Cover Letter Generation (depends on F-ANV-09, F-ANV-10)

- [x] **3.5 Cover letter generator** — Create logic to generate cover letter from CV + job description; Markdown primary output; non-generic (must reference actual projects from CV)
- [x] **3.6 Cover letter prompts** — Write prompts for `cover_letter` task in `src/anvilcv/ai/prompts/cover_letter/`
- [x] **3.7 Cover command** — Create `src/anvilcv/cli/cover_command/` — `anvil cover INPUT --job <path-or-url> [--provider] [--output]`
- [x] **3.8 Cover tests** — Tier 1 structural tests with mocked APIs; `tests/unit/test_cover.py`

---

## Cross-Cutting Concerns (Ongoing Throughout)

- [ ] **X.1 Vendor patch documentation** — Every vendored file modification gets an entry in `patches/README.md` with file, purpose, and risk level (Low/Medium/High)
- [ ] **X.2 Extend vendored `error_handler.py`** `[Extended]` — Add formatting for AI/API failure errors (exit codes 3, 4)
- [ ] **X.3 Extend vendored `sample_generator.py` and `sample_content.yaml`** `[Extended]` — Add Anvil-specific and developer-focused sample content for `anvil new`
- [ ] **X.4 Extend vendored `error_dictionary.yaml`** `[Extended]` — Add error messages for Anvil-specific validation failures
- [ ] **X.5 Test coverage target** — Maintain ≥80% line coverage on Anvil-specific code; 100% coverage on ATS scoring rules (P-01 through P-08, S-01 through S-08, K-01 through K-05) per `specs/success-criteria.md`
- [ ] **X.6 Ruff + mypy compliance** — All code passes `ruff check` and `mypy` on every commit
- [ ] **X.7 Compatibility corpus maintenance** — Grow corpus to ≥20 files covering all 5 themes and all entry types; include 5+ community contribution examples
- [ ] **X.8 Tier 2 golden-set regression tests** — Per `specs/testing-strategy.md`: 5-10 reference cases per AI feature (tailor, cover, prep); run against live APIs nightly; LLM-as-judge scoring ≥50/100 on ALL test cases for ALL supported providers; MANDATORY for feature completion

---

## Missing Specifications (Must Author Before Implementation)

- [ ] **S.1 `specs/devforge-theme.md`** — Detailed visual design spec for the devforge theme. Required by F-ANV-07 success criteria: "Design mockup or detailed design spec must precede implementation." Must define: layout grid, typography (font family, sizes, weights), color palette, skill chip rendering, project metadata line format, section header styling, spacing system, and responsive behavior for HTML output.

---

## Implementation Notes

### Vendored Import Resolution
- Python 3.12+ no longer calls `find_module` on meta-path finders; must use `find_spec`/`exec_module` API
- The `_VendorImporter` in `anvilcv/__init__.py` transparently redirects `rendercv.*` → `anvilcv.vendor.rendercv.*`
- This preserves all Untouched vendored files without rewriting their imports

### Missing Dependencies Discovered
- pyproject.toml was missing rendercv's transitive deps: `pydantic[email]`, `pydantic-extra-types`, `phonenumbers`, `markdown`, `annotated-doc`, `rendercv-fonts`, `packaging`
- These have been added to `dependencies` in pyproject.toml
- `ruff` config now excludes `src/anvilcv/vendor/` to avoid lint noise from vendored code

---

## Not Planned (P3 — Post-v1)

- F-ANV-14: Living Resume Monitor (`anvil watch`) — Deferred (stub only in CLI)
- F-ANV-15: Web Deployment (`anvil deploy`) — Deferred (stub only in CLI)

---

## Scaffolding Note

The `src/anvilcv/scoring/rules/` directory exists but is **unused scaffolding**. Scoring rules are implemented directly in `parsability_checker.py` (P-01 to P-08), `structure_checker.py` (S-01 to S-08), and `keyword_matcher.py` (K-01 to K-05). The `rules/` directory can be removed or repurposed.

---

## Implementation Order Summary

```
Phase 0: Foundation (sequential start, then parallel)
  0.1 Vendor patches → 0.2 __init__ → 0.3 __main__ → 0.4 entry_point
  0.5 config ─┐
  0.6 cache  ─┤ (parallel after 0.4)
  0.7 exceptions ─┘
  0.8 test infra (after 0.7)

Phase 1: P0 Features
  F-ANV-03 (CLI)     : 1.1 → 1.2 → 1.3 → 1.4 → 1.5
  F-ANV-01 (Render)  : 1.6 → 1.7 → 1.8 → 1.9
  F-ANV-09 (AI)      : 1.10 → 1.11 → 1.12 → 1.13 → 1.14 → 1.15 → 1.16 → 1.17
  F-ANV-02 (Schema)  : 1.18 → 1.19 → 1.20 → 1.21 → 1.22 → 1.23 → 1.24 → 1.25
  F-ANV-04 (Score)   : 1.26 → 1.27 → 1.28 → 1.29 → 1.30 → 1.31 → 1.32
  F-ANV-05 (Score+JD): 1.33 → 1.34 → 1.35 → 1.36 → 1.37 → 1.38

Phase 2: P1 Features
  F-ANV-06 (ATS HTML) : 2.1 → 2.2 → 2.3 → 2.4
  F-ANV-07 (devforge) : 2.5 → 2.6 → 2.7 → 2.8 → 2.9 → 2.10 → 2.11
  F-ANV-16 (JSON Sch) : 2.12 → 2.13
  F-ANV-17 (Export)   : 2.14 → 2.15
  F-ANV-08 (Variants) : 2.16 → 2.17 → 2.18
  F-ANV-10 (Tailor)   : 2.19 → 2.20 → 2.21 → 2.22 → 2.23 → 2.24
  F-ANV-11 (GitHub)   : 2.25 → 2.26 → 2.27 → 2.28 → 2.29 → 2.30

Phase 3: P2 Features
  F-ANV-12 (Prep)     : 3.1 → 3.2 → 3.3 → 3.4
  F-ANV-13 (Cover)    : 3.5 → 3.6 → 3.7 → 3.8
```

Parallelism opportunities within each phase:
- **Phase 0:** Tasks 0.1-0.4 sequential (entry point depends on patches); 0.5-0.7 can parallel after 0.4; 0.8 after 0.7
- **Phase 1:** F-ANV-03, F-ANV-01, and F-ANV-09 can all run in parallel (no shared deps); F-ANV-02 starts after F-ANV-01; F-ANV-04 starts after F-ANV-01; F-ANV-05 starts after F-ANV-04
- **Phase 2:** F-ANV-06, F-ANV-07 (after spec S.1), F-ANV-16, F-ANV-17, F-ANV-08 can largely parallel after their deps; F-ANV-10 needs both F-ANV-02 and F-ANV-09; F-ANV-11 needs F-ANV-02 only

## Vendored Files Reference

Quick reference for build agents — files classified by modification status:

**Modified (4):** Change internals, document in patches/README.md
- `vendor/rendercv/__init__.py` — package name + version
- `vendor/rendercv/__main__.py` — entry point redirect
- `vendor/rendercv/cli/entry_point.py` — binary entry point
- `vendor/rendercv/cli/app.py` — Typer app replacement

**Extended (13):** Add functionality, document in patches/README.md
- `vendor/rendercv/cli/error_handler.py` — AI/API error formatting
- `vendor/rendercv/cli/render_command/render_command.py` — `--variant`, `--no-ats-html` flags
- `vendor/rendercv/cli/render_command/run_rendercv.py` — ATS HTML generation step
- `vendor/rendercv/cli/new_command/` — Anvil-flavored YAML generation
- `vendor/rendercv/schema/json_schema_generator.py` — Anvil fields in schema
- `vendor/rendercv/schema/sample_generator.py` — Anvil sample content
- `vendor/rendercv/schema/sample_content.yaml` — developer-focused samples
- `vendor/rendercv/schema/error_dictionary.yaml` — Anvil error messages
- `vendor/rendercv/schema/models/rendercv_model.py` — AnvilModel subclass target
- `vendor/rendercv/schema/models/design/design.py` — devforge theme registration
- `vendor/rendercv/renderer/html.py` — ATS HTML output path
- `vendor/rendercv/renderer/path_resolver.py` — variant-aware paths
- `vendor/rendercv/renderer/templater/templater.py` — render_ats_html function

**Wrapped (1):** Use through adapter in new file
- `vendor/rendercv/schema/rendercv_model_builder.py` — AnvilModel builder adapter

**Everything else is Untouched — do NOT modify.**
