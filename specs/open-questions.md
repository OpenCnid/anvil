# Open Questions — All Resolved

All 8 open questions have been resolved and their decisions implemented across the spec files. This document records the decisions for reference.

## OQ-1: PDF Text Extraction Library ✅

**Decision:** `pdfminer.six` — MIT-licensed, pure Python, provides text position data for layout analysis (single-column detection, reading order).

**Rationale:** MIT-compatible (no license conflict), well-maintained, sufficient for ATS scoring needs. Switch to `pdfplumber` only if higher-level API proves valuable during implementation.

**Updated:** `ats-scoring-model.md`

## OQ-2: Job Description URL Parsing ✅

**Decision:** Multi-source input with graceful fallback:
- **URL** — Best-effort heuristic parsing via `readability-lxml`. Works for most static pages, may fail on SPAs.
- **File** — `--job ./path/to/job.txt` or `--job ./path/to/job.yaml`
- **Stdin** — `--job -` (piped text)

If URL parsing fails, error message tells user to save text and use file/stdin. No headless browser dependency.

**Updated:** `cli-interface.md`, `architecture.md`, `data-model.md`

## OQ-3: Vendoring vs. Dependency Approach ✅

**Decision:** Vendor + patch files. rendercv source is copied into `src/anvilcv/vendor/rendercv/` at a pinned release tag. Each modification is tracked as a documented patch in `patches/README.md`. This gives full control over modifications with clear traceability for upstream cherry-picks.

**Updated:** `architecture.md`, `fork-maintenance.md` (already described this approach — language tightened to definitive)

## OQ-4: Theme Implementation Scope ✅

**Decision:** Ship **one** theme for v1: `devforge`. Terminal theme deferred to post-v1.

**devforge design direction:**
- Clean, modern design targeting developers and indie hackers
- Skills rendered as inline chips (not bulleted lists)
- Projects with GitHub-style metadata line (★ stars · language · last updated)
- ATS-safe single-column layout with standard sections
- Design mockup or detailed design spec must precede implementation

**Updated:** `feature-tracker.md` (F-ANV-07), `architecture.md` (theme directory)

## OQ-5: Ollama Model Testing Matrix ✅

**Decision:** Tested set is `llama3.1:8b` and `llama3.1:70b`. All other Ollama models (mistral, codellama, phi-3, etc.) are accepted but classified as community-contributed/best-effort. Anvil logs a warning when using an untested model.

**Rationale:** Testing every model is impractical. Two models (small + large) cover the primary use cases. Community can contribute test results for other models.

**Updated:** `ai-provider-abstraction.md`

## OQ-6: Rate Limit Strategy for GitHub Scan ✅

**Decision:** Conditional requests (ETag/If-None-Match) + aggressive caching in `.anvil/github/` with TTL + `--max-repos 100` default. On first scan, warn if user has many repos and scan will take time. Re-scans use conditional requests so cached repos don't consume API calls.

**Updated:** `cli-interface.md` (scan error behavior), `architecture.md` (github module), `feature-tracker.md` (F-ANV-11)

## OQ-7: Cover Letter and Prep Output Format ✅

**Decision:** Markdown for both cover letter and interview prep. PDF rendering for cover letter is a P2 stretch goal (requires a cover letter Typst template, reusing the existing rendering pipeline). DOCX is out of scope for v1.

**Updated:** `cli-interface.md` (cover command), `feature-tracker.md` (F-ANV-12, F-ANV-13), `data-model.md` (data flow table)

## OQ-8: Vercel Deployment Architecture ✅

**Decision:** Static HTML. The simplest approach:
- Responsive HTML version of the resume
- Downloadable PDF link (hosted alongside)
- Minimal CSS (no JavaScript required for content)
- SEO meta tags (og:title, og:description)
- No serverless functions, no dynamic rendering

**Updated:** `architecture.md` (web_deploy.py), `feature-tracker.md` (F-ANV-15)
