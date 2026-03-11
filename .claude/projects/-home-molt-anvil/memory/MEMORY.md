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

## Implementation Status (v0.0.12, 521 tests)
- **Phase 0**: Complete (foundation, vendor patches, CLI scaffold)
- **Phase 1**: Complete (F-ANV-01, F-ANV-02, F-ANV-03, F-ANV-04, F-ANV-05, F-ANV-09)
- **Phase 2**: Nearly complete (F-ANV-06 complete, F-ANV-08, F-ANV-10, F-ANV-11, F-ANV-16, F-ANV-17)
- **Phase 3**: Complete (F-ANV-12, F-ANV-13)
- **Remaining**: F-ANV-07 (devforge theme, blocked on spec S.1), cross-cutting X.1-X.8

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
