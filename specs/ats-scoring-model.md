# ATS Scoring Model

## Scope and Honesty Statement

**What the ATS scorer IS:** A heuristic keyword and structure analyzer that evaluates resume content against known best practices for ATS compatibility. It catches common problems that cause parsing failures and suggests improvements.

**What the ATS scorer IS NOT:** A simulator of any commercial ATS. It cannot replicate the proprietary parsing behavior of Greenhouse, Lever, Workday, Taleo, iCIMS, or any other ATS vendor. No public specification exists for how these systems parse resumes. Any tool that claims to "simulate" ATS parsing is misleading.

**Confidence framework:** Every scoring rule is classified as one of:
- **Evidence-based** — Cites a specific study, reverse-engineering analysis, or documented ATS vendor guidance
- **Opinionated heuristic** — Best-practice recommendation based on resume industry consensus without ground truth from any ATS vendor

Users and build agents see these classifications in the score report.

## Scoring Architecture

The ATS scorer operates on **rendered output** (PDF or HTML), not raw YAML. This is intentional — it evaluates what the ATS will actually see.

```
Rendered PDF/HTML → Text Extraction → Parsability Checks → Section Detection → Keyword Analysis → Score Report
```

### Input Handling

| Input | Processing |
|-------|-----------|
| PDF file | Extract text via `pdfminer.six` (MIT-licensed, pure Python). Preserves text position data for layout analysis (single-column detection, reading order). |
| HTML file | Extract text content from DOM. Evaluate semantic structure. |
| YAML file | Render first (using `anvil render`), then score the rendered output. |

## Scoring Categories

### 1. Parsability Score (0-100)

Evaluates whether the resume's structure can be reliably parsed by text extraction tools.

| Rule | Check | Confidence | Source/Citation |
|------|-------|-----------|----------------|
| P-01: Single-column layout | Detect multi-column layout via text position analysis | Evidence-based | Jobscan 2023 ATS parsing study; TopResume 2022 ATS formatting guide |
| P-02: No embedded images for text | Check if text content is extractable (not rasterized) | Evidence-based | Greenhouse support docs: "Ensure all text is machine-readable" |
| P-03: Standard fonts | Check if fonts are embeddable and commonly supported | Opinionated heuristic | Industry consensus; no ATS vendor specifies font requirements |
| P-04: No tables for layout | Detect HTML table elements or PDF table structures used for layout | Evidence-based | Jobscan 2023: "Tables can cause parsing issues in 30%+ of ATS systems" |
| P-05: No headers/footers for critical content | Check if name/contact info is in the main body, not headers/footers | Evidence-based | Workday support: "Content in headers and footers may not be parsed" |
| P-06: Text extractability | Verify that text can be extracted in reading order | Evidence-based | Fundamental to any text-based parsing |
| P-07: No text boxes or floating elements | Detect positioned elements that break reading order | Opinionated heuristic | Common advice; severity varies by ATS |
| P-08: Standard file format | PDF/A or standard PDF (not scanned image) | Evidence-based | Most ATS vendors require machine-readable PDFs |

### 2. Structure Score (0-100)

Evaluates whether standard resume sections are present and detectable.

| Rule | Check | Confidence | Source/Citation |
|------|-------|-----------|----------------|
| S-01: Contact information present | Detect name, email, phone, location | Evidence-based | Universal ATS requirement |
| S-02: Experience section detected | Look for section header matching "Experience", "Work History", "Employment", etc. | Evidence-based | Standard ATS section mapping |
| S-03: Education section detected | Look for section header matching "Education", "Academic Background", etc. | Evidence-based | Standard ATS section mapping |
| S-04: Skills section detected | Look for "Skills", "Technical Skills", "Technologies", etc. | Opinionated heuristic | Not all ATS require a skills section; most benefit from it |
| S-05: Standard section headers | Check if section headers use conventional names vs. creative alternatives | Opinionated heuristic | "What I've Done" vs. "Experience" — ATS may miss creative headers |
| S-06: Chronological date ordering | Check if entries within sections are reverse-chronological | Opinionated heuristic | Most ATS parse dates and expect reverse-chronological order |
| S-07: Machine-readable dates | Check date format consistency (e.g., "January 2024" vs. "Jan '24" vs. "1/24") | Opinionated heuristic | Full month names are safest but not required |
| S-08: Resume length | Check page count (1-2 pages for most candidates) | Opinionated heuristic | Industry best practice, not ATS-specific |

### 3. Keyword Match Score (0-100) — Requires Job Description

Only calculated when a job description is provided via `--job`.

| Rule | Check | Confidence | Source/Citation |
|------|-------|-----------|----------------|
| K-01: Required skill keywords | Match job's required skills against resume content | Evidence-based | ATS keyword matching is documented by Greenhouse, Lever |
| K-02: Preferred skill keywords | Match job's preferred/nice-to-have skills | Evidence-based | Same as above |
| K-03: Job title alignment | Check if resume contains the target job title or close synonyms | Opinionated heuristic | Some ATS weight title matches; extent varies |
| K-04: Industry terminology | Check for industry-specific terms from the job description | Opinionated heuristic | Keyword density analysis |
| K-05: Action verb usage | Check for strong action verbs ("built", "led", "shipped" vs. "responsible for") | Opinionated heuristic | Resume writing best practice |

### Keyword Extraction

Job description keywords are extracted using a **heuristic pipeline** (no AI required):

1. **Section detection** — Identify "Requirements", "Qualifications", "What you'll do" sections
2. **Skill extraction** — Match against a curated skill taxonomy (programming languages, frameworks, tools, certifications)
3. **Requirement parsing** — Extract "X years of experience with Y" patterns
4. **Deduplication** — Normalize skills ("k8s" = "Kubernetes" = "kubernetes")

The skill taxonomy is stored as a YAML file (`src/anvilcv/scoring/skills_taxonomy.yaml`) containing:
- ~500 common technical skills with aliases
- Categorized by domain (languages, frameworks, cloud, databases, tools, methodologies)
- Version-controlled and extensible by users

Example taxonomy structure:
```yaml
# skills_taxonomy.yaml (excerpt)
languages:
  - name: Python
    aliases: ["python", "python3", "py"]
  - name: Go
    aliases: ["go", "golang"]
  - name: JavaScript
    aliases: ["javascript", "js", "ecmascript"]
  - name: TypeScript
    aliases: ["typescript", "ts"]

cloud:
  - name: AWS
    aliases: ["aws", "amazon web services", "amazon cloud"]
  - name: Kubernetes
    aliases: ["kubernetes", "k8s", "kube"]
  - name: Terraform
    aliases: ["terraform", "tf", "hcl"]

tools:
  - name: Docker
    aliases: ["docker", "containerization", "containers"]
  - name: Git
    aliases: ["git", "version control"]

certifications:
  - name: AWS Solutions Architect
    aliases: ["aws sa", "aws solutions architect", "aws certified solutions architect"]
```

Build agents: the taxonomy file is the ONLY source of keyword aliases. Do not hardcode skill aliases in scoring logic.

**Optional AI-enhanced extraction:** When an AI provider is configured, `anvil score --job` can use LLM-based extraction for better results on non-standard job descriptions. The AI path is never required — heuristic extraction always works.

## Score Calculation

### Overall Score

```
overall = (parsability * 0.40) + (structure * 0.30) + (keyword_match * 0.30)
```

If no job description is provided, keyword_match is omitted and weights are:

```
overall = (parsability * 0.55) + (structure * 0.45)
```

### Per-Category Scores

Each category score is calculated as:

```
category_score = (passing_rules / total_rules) * 100
```

Rules are not weighted within categories for v1. Each rule passes or fails (with "warn" treated as a partial pass at 0.5 weight).

### Score Interpretation

| Score | Label | Meaning |
|-------|-------|---------|
| 90-100 | Excellent | Resume follows all detected best practices |
| 75-89 | Good | Minor improvements possible |
| 50-74 | Fair | Significant issues that may affect ATS parsing |
| 0-49 | Poor | Major structural or parsability problems |

## Known Limitations

1. **No ground truth.** Scores are heuristic estimates. A score of 90 does not guarantee any ATS will parse the resume correctly. A score of 50 does not guarantee it will fail.

2. **PDF text extraction quality varies.** Complex PDF layouts may extract text in wrong order. This is a limitation of PDF as a format, not the scorer.

3. **Keyword matching is literal.** The heuristic keyword matcher does exact and alias matching. It does not understand that "built distributed systems" implies "distributed systems architecture" unless the alias is in the taxonomy.

4. **Job description parsing is best-effort.** Job description pages vary wildly in structure. The URL fetcher uses heuristic parsing to extract the job description text from a web page. It may include navigation, footer, or unrelated content.

5. **English-only for v1.** Keyword extraction and skill taxonomy are English-language. Non-English resumes and job descriptions will score poorly on keyword matching.

6. **No visual evaluation.** The scorer evaluates text content and structure, not visual design. A visually cluttered resume with good text structure may score well.

## Output Format

Terminal output uses color-coded results:

```
$ anvil score Jane_Developer_CV.pdf --job https://acme.com/careers/sre

╭──────────────────────────────────────╮
│        ATS Compatibility Report       │
│           Score: 78/100               │
╰──────────────────────────────────────╯

Parsability: 90/100  ████████████████████░░
  ✓ Single-column layout                [evidence-based]
  ✓ All text machine-readable           [evidence-based]
  ✓ No tables for layout                [evidence-based]
  ⚠ Date format inconsistency           [opinionated heuristic]
    "Jan 2024" on line 12; prefer "January 2024"

Structure: 85/100  ██████████████████░░░░
  ✓ Contact info complete
  ✓ Experience section detected
  ✓ Education section detected
  ✓ Skills section detected
  ⚠ Resume is 2 pages (1 page recommended for < 10 years)

Keywords: 65/100  ████████████████░░░░░░
  Matched: Python, Go, Kubernetes (3/5 required)
  Missing: Terraform, SRE
  ──────
  ⬆ HIGH: Add "Terraform" to skills section
  ⬆ MED:  Add "SRE" or "Site Reliability" to headline
  ⬇ LOW:  Use full month names in dates
```
