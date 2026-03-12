# Feature Tracker

## Priority Key

- **P0** — Launch blocker. Anvil cannot ship without this.
- **P1** — v1 must-have. Required for the v1 release.
- **P2** — v1 nice-to-have. Included if time permits, otherwise post-v1.
- **P3** — Post-v1. Explicitly deferred.

## Classification Key

- **Core** — Works with zero configuration. No API keys, no tokens, no accounts, no internet required.
- **Extended** — Requires user-provided API keys or tokens. Degrades gracefully without them.

## Feature Table

| ID | Name | Description | Class | Priority | Dependencies | Success Criteria |
|----|------|-------------|-------|----------|--------------|------------------|
| F-ANV-01 | Forward-Compatible Rendering | Anvil renders any valid rendercv v2.7 YAML file, producing output identical to rendercv | Core | P0 | None | 100% of rendercv example YAML files in the compatibility corpus render without errors. Typst output is byte-identical to rendercv output for the same input. |
| F-ANV-02 | Extended YAML Schema | Anvil adds the `anvil` top-level section to the YAML schema without breaking rendercv compatibility | Core | P0 | F-ANV-01 | rendercv YAML without `anvil` section validates and renders identically. YAML with `anvil` section validates against Anvil's extended schema. Unknown fields in `anvil` produce clear validation errors. |
| F-ANV-03 | CLI Scaffold | The `anvil` binary with subcommands: render, new, score, tailor, scan, prep, cover, watch, deploy | Core | P0 | None | `anvil --help` lists all subcommands. `anvil render` works identically to `rendercv render` for rendercv YAML files. Each subcommand has `--help` output. |
| F-ANV-04 | ATS Score Checker | `anvil score` parses rendered resume and outputs heuristic ATS compatibility report | Core | P0 | F-ANV-01 | Scores a rendered PDF or HTML file. Outputs parsability, structure, and keyword match scores (0-100). Each scoring rule is classified as evidence-based or opinionated-heuristic. Runs without API keys. |
| F-ANV-05 | ATS Score with Job Description | `anvil score --job <file-or-url>` scores resume against a specific job description | Core | P0 | F-ANV-04 | Keyword extraction from job description text. Keyword match percentage calculated. Missing keywords listed with priority. Job description can be provided as URL (fetched and parsed) or file path. |
| F-ANV-06 | ATS-First HTML Output | Semantic HTML output with `section`/`article`/`h1-h3` markup designed for ATS parsing | Core | P1 | F-ANV-01 | `anvil render` produces `_ats.html` alongside standard outputs. HTML uses semantic elements (`<section>`, `<article>`, `<h1>`-`<h3>`). All text content is in the DOM (no CSS-only content). HTML passes W3C validation. |
| F-ANV-07 | Modern Engineer Theme | Developer/AI-builder focused Typst theme: **devforge** (v1). Terminal theme deferred to post-v1. | Core | P1 | F-ANV-01 | `devforge` theme available via `design.theme` in YAML. Clean, modern design: skills rendered as inline chips (not bulleted lists), projects with GitHub-style metadata line (★ stars · language · last updated), ATS-safe single-column layout with standard sections. Theme renders correctly for all rendercv entry types (education, experience, normal, bullet, numbered, one_line, publication, text). Unique Pydantic design model. Produces valid Typst, Markdown, and HTML output. Snapshot tests pass with the sample CV. Design mockup or detailed design spec must precede implementation. |
| F-ANV-08 | Multi-Variant Rendering | Render multiple tailored YAML variants in one command | Core | P1 | F-ANV-02 | `anvil render --variant <dir>` renders all YAML files in a variant directory. Each variant produces its own output set. Variant provenance metadata is preserved in output filenames. |
| F-ANV-09 | AI Provider Abstraction | Pluggable provider interface supporting Anthropic, OpenAI, and Ollama | Extended | P0 | None | Provider interface defined with methods for text generation and structured output. Each provider implements the interface. Provider selection via `anvil.providers.default` config or `--provider` flag. Missing API key produces clear error with setup instructions (not a stack trace). |
| F-ANV-10 | AI Job Tailoring | `anvil tailor --job <url-or-file>` produces a tailored variant YAML | Extended | P1 | F-ANV-02, F-ANV-09 | Takes source YAML + job description (URL or file). Produces new YAML file in variants directory. Variant includes provenance metadata (source, job, timestamp, changes). Bullets are rewritten to match job language. Projects are reordered by relevance. Original YAML is never modified. |
| F-ANV-11 | GitHub Content Scanner | `anvil scan --github <user>` crawls GitHub repos and generates project entries | Extended | P1 | F-ANV-02 | Fetches repo metadata via GitHub API. Extracts languages, commit counts, stars, topics. Generates YAML project entries with real metrics. Default `--max-repos 100`. Uses conditional requests (ETag/If-None-Match) to minimize API calls on re-scans. Aggressive caching in `.anvil/github/` with TTL. Warns if user has many repos and scan will take time. Requires GitHub token for useful rate limits (authenticated: 5000 req/hr; unauthenticated: 60 req/hr). |
| F-ANV-12 | Interview Prep | `anvil prep --job <url-or-file>` generates per-project talking points | Extended | P2 | F-ANV-09, F-ANV-10 | Generates **Markdown** file with talking points for each project/experience entry. Points are matched to job requirements. Format: "If they ask about X, lead with Y from project Z." Requires AI provider. |
| F-ANV-13 | Cover Letter Generation | `anvil cover --job <url-or-file>` generates a cover letter from CV + job description | Extended | P2 | F-ANV-09, F-ANV-10 | Generates cover letter as **Markdown** (primary output). PDF rendering via `--render` is a P2 stretch goal (requires a cover letter Typst template). Pulls specific project evidence from CV. Non-generic (references actual projects and skills). DOCX output is out of scope for v1. Requires AI provider. |
| F-ANV-14 | Living Resume Monitor | `anvil watch` monitors GitHub for new activity and suggests resume updates | Extended | P3 | F-ANV-11 | Polls GitHub API at configurable interval. Detects new repos, significant commits, releases. Outputs digest to terminal or file. Does not auto-modify resume YAML. |
| F-ANV-15 | Web Deployment | `anvil deploy` renders resume as **static HTML** site and deploys to Vercel | Extended | P3 | F-ANV-01, F-ANV-06 | Deploys a static site: responsive HTML resume + downloadable PDF link (hosted alongside) + minimal CSS (no JavaScript required for content) + SEO meta tags (og:title, og:description). No serverless functions, no dynamic rendering. Deploys to Vercel via API. Supports custom domain configuration. Requires Vercel token. |
| F-ANV-16 | JSON Schema Generation | Generate JSON Schema for Anvil's extended YAML format for editor autocompletion | Core | P1 | F-ANV-02 | JSON Schema covers all Anvil-specific fields. Works with VS Code YAML extension. Includes descriptions and examples for all fields. |
| F-ANV-17 | rendercv Export | `anvil export --rendercv` strips the `anvil` section to produce rendercv-compatible YAML | Core | P1 | F-ANV-02 | Input: Anvil YAML with `anvil` section. Output: YAML without `anvil` section that passes rendercv validation. All other sections preserved byte-identical. |

## Dependency Graph (Simplified)

```
F-ANV-01 (Rendering) ← F-ANV-02 (Schema) ← F-ANV-10 (Tailoring)
                                            ← F-ANV-08 (Multi-Variant)
                     ← F-ANV-04 (ATS Score) ← F-ANV-05 (Score + JD)
                     ← F-ANV-06 (ATS HTML)
                     ← F-ANV-07 (Themes)

F-ANV-09 (AI Provider) ← F-ANV-10 (Tailoring) ← F-ANV-12 (Prep)
                                                ← F-ANV-13 (Cover)
                        ← F-ANV-12 (Prep)
                        ← F-ANV-13 (Cover)

F-ANV-11 (GitHub Scan) ← F-ANV-14 (Watch)

F-ANV-03 (CLI) — required by all commands
F-ANV-16 (JSON Schema) — depends on F-ANV-02
```

## Priority Dependency Validation

No circular dependencies exist. No feature depends on a feature of lower priority:

- P0 features depend only on other P0 features or no features
- P1 features depend only on P0 or P1 features
- P2 features depend on P0 or P1 features
- P3 features depend on P0 or P1 features

Verified: F-ANV-12 (P2) depends on F-ANV-09 (P0) and F-ANV-10 (P1) — valid. F-ANV-14 (P3) depends on F-ANV-11 (P1) — valid. No inversions.
