## Build & Run

Python 3.12+ project. Package name: `anvilcv`. CLI binary: `anvil`.

```bash
# Install in dev mode (from project root)
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"
```

## Validation

Run these after implementing to get immediate feedback:

- Tests: `pytest tests/ -x --numprocesses=auto`
- Typecheck: `mypy src/anvilcv/ --ignore-missing-imports`
- Lint: `ruff check src/ tests/`
- Format check: `ruff format --check src/ tests/`

## Operational Notes

- Source code lives in `src/anvilcv/` (NOT `src/` directly)
- Vendored rendercv v2.7 lives at `src/anvilcv/vendor/rendercv/` — do NOT modify files in there unless the architecture spec (specs/architecture.md) classifies them as Modified or Extended
- Baseline copy at `baseline/rendercv-v2.7/` for fork integrity checks
- Import vendored code via `anvilcv.vendor.rendercv`, NEVER via `rendercv` directly
- New Anvil code goes in `src/anvilcv/`, not in the vendor tree
- The `anvil` CLI entry point is at `src/anvilcv/cli/entry_point.py`

### Dependency Management
- Always activate venv first: `source .venv/bin/activate`
- After modifying pyproject.toml deps, reinstall: `pip install -e ".[dev]"`
- Vendored rendercv requires deps not in rendercv's public extras: `pydantic[email]`, `pydantic-extra-types`, `phonenumbers`, `markdown`, `annotated-doc`, `rendercv-fonts`, `packaging`
- Ruff excludes `src/anvilcv/vendor/` — only Anvil code is linted

### Virtual Environment
- Venv at `.venv/` — use `source .venv/bin/activate` before any command
- Install: `pip install -e ".[dev]"` (or `pip install -e ".[full]"` for PDF rendering)

### Codebase Patterns

- Pydantic v2 models for all data validation (inheriting from rendercv's pattern)
- Typer for CLI commands
- Jinja2 templates for rendering (Typst, Markdown, HTML)
- `src/anvilcv/vendor/rendercv/` is the vendored upstream — treat as read-only unless spec says otherwise

### Theme Template Lookup

- `render_single_template()` in `templater.py` tries `{theme_name}/{template_path}` first, then `{file_type}/{template_path}` — works for ALL formats (Typst, Markdown, HTML)
- Theme templates go in `src/anvilcv/themes/{theme_name}/` (NOT in the vendor tree)
- Devforge theme: model at `themes/devforge/theme.py`, Typst templates in `themes/devforge/entries/*.j2.typ`, Markdown templates in `themes/devforge/*.j2.md` and `entries/*.j2.md`, HTML template at `themes/devforge/Full.html`

### Extended Vendored Files

When extending a vendored file: (1) add to MODIFIED_FILES in `tests/integration/test_fork_integrity.py`, (2) add entry in `patches/README.md`, (3) run `ruff check --fix` on the file (import sorting frequently breaks)

### Score Command Testing

The score command uses a two-step flow: `extract_text()` → `score_extracted_document()`. When mocking in tests, mock both `anvilcv.scoring.text_extractor.extract_text` (returns `ExtractedDocument`) and `anvilcv.scoring.ats_scorer.score_extracted_document` (returns `ScoreReport`). Do NOT mock `score_document` — the command no longer calls it directly.
