# Problem Statement

## The Resume Gap for Technical Practitioners

Software engineers, ML engineers, and full-stack developers face a specific set of resume problems that generic tools don't solve:

### 1. Format Lock-In Destroys Version Control

Most resume tools (Google Docs, Canva, Overleaf, Figma templates) produce opaque binary or proprietary formats. Engineers can't `git diff` a `.docx`. They can't review a Pull Request for a resume update. They can't branch a resume for a specific job application and merge improvements back. The resume — a document that changes dozens of times over a career — gets none of the tooling engineers apply to every other text artifact they produce.

**Cost:** Engineers maintain multiple divergent copies, lose track of what was sent where, and can't systematically improve their resume over time.

### 2. ATS Black Boxes Reject Qualified Candidates

Applicant Tracking Systems (Greenhouse, Lever, Workday, Taleo) parse uploaded resumes into structured data. Their parsers are proprietary and undocumented. Pretty-looking PDF resumes with custom layouts, multi-column designs, or embedded graphics often parse into garbage — missing sections, garbled text, lost formatting. Engineers who build beautiful things get punished by systems that can't read them.

**Cost:** Qualified candidates get auto-rejected before a human sees their resume. Engineers have no way to verify whether their resume will parse correctly before submitting.

### 3. Tailoring Is Manual and Doesn't Scale

Each job application ideally gets a tailored resume — different emphasis, reordered projects, rewritten bullets to match the job description's language. In practice, engineers maintain 1-3 generic versions because manual tailoring takes 30-60 minutes per application and the results aren't systematically tracked.

**Cost:** Engineers either send generic resumes (lower match rates) or spend hours on per-application customization that's discarded after submission.

### 4. GitHub Activity Doesn't Transfer to Resume Content

Engineers build real things — open source contributions, side projects, production systems — with quantifiable metrics (stars, test coverage, commit frequency, language breakdown). None of this automatically flows into their resume. They manually approximate: "Contributed to X" instead of "Shipped 47 PRs across 3 releases, adding 12K lines of Go with 89% test coverage."

**Cost:** Resumes underrepresent what engineers actually built. Metrics that would differentiate candidates stay locked in GitHub.

### 5. Existing Tools Make the Wrong Trade-Offs

| Tool | Problem |
|------|---------|
| Google Docs / Word | No version control, no automation, bad typography |
| LaTeX templates | Steep learning curve, brittle, poor ATS parsing |
| Canva / Figma | Visual-first design that ATS can't parse |
| LinkedIn export | Garbage formatting, no customization |
| JSON Resume | Good idea, weak execution, tiny ecosystem |
| rendercv | Closest match — YAML input, great typography, version-controllable — but no ATS awareness, no AI tailoring, no GitHub integration, academic-focused themes |

## What rendercv Gets Right

rendercv (v2.7, MIT license, actively maintained) solves the format problem correctly:

- **YAML input** — plain text, version-controllable, diffable
- **Typst rendering** — professional typography without LaTeX complexity
- **JSON Schema** — editor autocompletion and inline docs
- **Strict validation** — clear error messages before rendering
- **Multiple outputs** — PDF, Typst source, Markdown, HTML, PNG
- **Watch mode** — live reload during editing
- **Theme system** — 5 built-in themes, custom theme support
- **Locale support** — i18n for date formatting and section headers

## What rendercv Doesn't Solve

rendercv is a rendering engine. It takes static YAML input and produces static output. It has no awareness of:

- **Job descriptions** — can't tailor content to a specific role
- **ATS compatibility** — can't evaluate whether output will parse correctly
- **GitHub activity** — can't pull real metrics from source
- **Multi-variant management** — no built-in way to track which version went where
- **Interview preparation** — no connection between resume content and talking points

## Anvil's Thesis

Fork rendercv's proven rendering pipeline. Keep everything it does well. Add the intelligence layer that turns a static document into an adaptive system:

1. **Score before you submit** — Heuristic ATS checking catches problems before they cost you an interview
2. **Tailor without rewriting** — AI reads the job description, rewrites your bullets, reorders your projects
3. **Pull from source** — GitHub integration generates resume content from what you actually built
4. **Track your variants** — One source YAML, many tailored outputs, each linked to a specific application
5. **Stay in the terminal** — No web UI, no accounts, no sign-ups for core features

The target user opens a terminal, types `anvil tailor --job <url>`, and gets a tailored resume in seconds — rendered with the same typographic quality rendercv provides, optimized for the ATS that will parse it, with content that reflects real work.
