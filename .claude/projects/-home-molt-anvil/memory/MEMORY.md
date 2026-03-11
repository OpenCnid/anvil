# AnvilCV Project Memory

## Project Overview
AnvilCV is a developer-native AI-powered resume engine forked from rendercv v2.7. The vendored rendercv lives at `src/anvilcv/vendor/rendercv/` with a meta-path import hook redirecting `rendercv.*` → `anvilcv.vendor.rendercv.*`.

## Key Architecture Patterns
- **Pydantic v2** for all data validation; `BaseModelWithoutExtraKeys` with `extra="forbid"`
- **AnvilModel extends RenderCVModel** — adds optional `anvil` and `variant` fields
- **Vendored file categories**: Modified (4), Extended (13), Wrapped (1), Untouched (everything else)
- **CLI**: Typer app in `src/anvilcv/cli/app.py`, commands registered via imports in `entry_point.py`
- **AI Provider ABC**: `src/anvilcv/ai/provider.py` with Anthropic/OpenAI/Ollama implementations
- **ruamel.yaml** for format-preserving YAML operations

## Tool & Environment Notes
- Use `.venv/bin/ruff` for linting (not `uv`)
- Use `.venv/bin/python -m pytest` for tests
- No git remote configured — local commits and tags only
- `typst` binary available for PDF generation
- ruff config excludes `src/anvilcv/vendor/`

## Implementation Status (v0.0.13, 544 tests)
- **Phase 0-1**: Complete
- **Phase 2**: F-ANV-06 complete, F-ANV-07 core done (Typst only; MD/HTML templates pending), F-ANV-08/10/11/16/17 complete
- **Phase 3**: Complete (F-ANV-12, F-ANV-13)
- **Remaining**: F-ANV-07 tasks 2.8-2.9 (MD/HTML templates), cross-cutting X.1-X.8

## Devforge Theme Notes
- DevforgeTheme must have `sections` (with `show_time_spans_in`) and `header.connections` sub-models — model_processor and connections.py access these
- Templates at `src/anvilcv/themes/devforge/` — Jinja2 loader searches `_anvil_themes_directory`
- Devforge uses shared markdown/HTML templates (only Typst is theme-specific)

## Common Lint Issues
- I001: Import block sorting — fix with `ruff check --fix`
- F401: Unused imports — common in test files
- E501: Line too long (>100 chars) — split strings or CSS lines

## Test Patterns
- Async tests use `asyncio.run()` in sync test functions (no pytest-asyncio)
- `GenerationResponse` requires: content, model, provider, input_tokens, output_tokens
- Phone numbers in corpus use `phonenumbers` validation — avoid 555 numbers
- Corpus files in `tests/corpus/`, integration tests in `tests/integration/`

## File Reference
- See `IMPLEMENTATION_PLAN.md` for detailed task tracking
- See `specs/` for feature specs, architecture, CLI interface, data model
