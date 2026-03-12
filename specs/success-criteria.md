# Success Criteria

## v1 Release — "Done" Definition

v1 is shippable when ALL of the following are true:

### Functional Requirements

1. **Forward compatibility:** 100% of the compatibility corpus (≥20 rendercv YAML files) renders through Anvil with byte-identical Typst, Markdown, and HTML output compared to rendercv v2.7.

2. **CLI completeness:** All P0 and P1 features are implemented, passing Tier 1 tests, and have `--help` documentation. Specifically:
   - `anvil render` works identically to `rendercv render` for all rendercv YAML
   - `anvil new` generates valid Anvil-extended YAML
   - `anvil score` produces a heuristic ATS report for any rendered resume
   - `anvil score --job` adds keyword matching from job descriptions
   - `anvil tailor` produces tailored variant YAML with provenance metadata
   - `anvil scan` fetches GitHub data and generates project entries
   - ATS-optimized HTML output is generated alongside standard output
   - At least 1 new developer-focused theme is functional (devforge; terminal theme deferred to post-v1 per OQ-4)

3. **AI provider support:** At least 2 providers (Anthropic + OpenAI) pass Tier 2 golden-set regression tests with scores ≥ 60/100 on all test cases. Ollama is functional but best-effort.

4. **Error handling:** Every extended feature produces a clear, actionable error message (not a stack trace) when invoked without required API keys.

5. **JSON Schema:** Anvil's extended YAML schema has a generated JSON Schema that enables autocompletion in VS Code.

### Quality Requirements

6. **Test coverage:** ≥ 80% line coverage on Anvil-specific code (`src/anvilcv/` excluding `vendor/`). 100% of ATS scoring rules have unit tests.

7. **Documentation:** README with installation instructions, quick-start guide, and feature overview. Each CLI command has `--help` text.

8. **Packaging:** `pip install "anvilcv[full]"` works on Python 3.12, 3.13, and 3.14. `anvil` binary is available after installation. Package is published to PyPI as `anvilcv`.

### Process Requirements

9. **Tier 3 human review:** All 3 fixed test cases (tailor, cover, prep) pass human review.

10. **Fork hygiene:** Module inventory is up to date. Patch index documents all modifications to vendored code.

## 1-Month Post-Release

Indicators of a healthy early-stage open source project:

| Metric | Target | How to Measure |
|--------|--------|---------------|
| GitHub stars | ≥ 50 | GitHub repo |
| PyPI downloads | ≥ 500 total | PyPI stats |
| Open issues | ≤ 20 (not indicating quality — indicating engagement) | GitHub issues |
| Critical bugs | 0 unresolved P0 bugs | Issue tracker |
| Contributor PRs | ≥ 1 external PR (even docs/typos) | GitHub PRs |
| rendercv compatibility | 100% corpus pass rate maintained | CI |

## 3-Month Post-Release

| Metric | Target | How to Measure |
|--------|--------|---------------|
| GitHub stars | ≥ 200 | GitHub repo |
| PyPI downloads | ≥ 3,000 total | PyPI stats |
| Active themes | ≥ 4 (2 built-in + 2 community) | Theme registry |
| Provider coverage | 3 tested providers (Anthropic, OpenAI, Ollama) | Tier 2 test results |
| Upstream sync | ≤ 1 rendercv release behind | Fork maintenance log |
| Documentation | Complete user guide on docs site | docs.anvilcv.com |

## 6-Month Post-Release

| Metric | Target | How to Measure |
|--------|--------|---------------|
| GitHub stars | ≥ 500 | GitHub repo |
| PyPI downloads | ≥ 10,000 total | PyPI stats |
| Contributors | ≥ 5 unique contributors | GitHub insights |
| P2 features shipped | ≥ 1 of (interview prep, cover letter) | Release notes |
| Skills taxonomy | ≥ 1,000 skills with aliases | skills_taxonomy.yaml line count |
| User testimonials | ≥ 3 public mentions (blog posts, tweets, HN) | Manual tracking |

## Anti-Goals (What Success Is NOT)

- **Not trying to be the biggest resume tool.** Anvil targets a niche (terminal-native developers). Success is depth of value for that audience, not breadth.
- **Not measured by feature count.** Shipping 5 features well beats shipping 10 features poorly.
- **Not dependent on AI.** If every AI provider shut down tomorrow, `anvil render` and `anvil score` still work. Core features are the foundation.
- **Not about monetization.** v1 is fully open source with no paid tier. Success is adoption and community, not revenue.
