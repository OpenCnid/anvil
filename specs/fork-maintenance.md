# Fork Maintenance Strategy

## Fork Base

**Base tag:** rendercv v2.7 (released 2026-03-06, commit `53c7343`)
**Fork location:** `src/anvilcv/vendor/rendercv/`

## Upstream Tracking Policy

### Frequency

Check rendercv releases **quarterly** or when a major release is announced. Not continuously. Tracking every commit or nightly build introduces noise without value.

Trigger conditions for an unscheduled upstream check:
- rendercv announces a breaking change or major feature
- A user reports a rendercv bug fix they need in Anvil
- rendercv changes a dependency version that conflicts with Anvil's

### Evaluation Process

When a new rendercv release is available:

1. **Read the changelog.** Identify which modules are affected.
2. **Cross-reference with the module inventory.** For each changed file:
   - If the module is **Untouched** in Anvil: Safe to cherry-pick. Apply the update.
   - If the module is **Extended**: Review the diff. If the change doesn't conflict with Anvil's additions, cherry-pick. If it does, merge manually.
   - If the module is **Modified**: Do NOT auto-apply. Review manually. File an issue to track the conflict.
   - If the module is **Wrapped**: Check if the wrapper's assumptions still hold. Usually safe to update.
3. **Run the compatibility corpus.** All corpus tests must pass after any upstream change.
4. **Run Anvil's full test suite.** Any regression is a blocker.

### Merge/Cherry-Pick Policy

- **Never auto-merge upstream changes.** Every change is evaluated manually.
- **Cherry-pick individual commits** from upstream when possible. Do not merge entire branches.
- **Skip releases that only touch Untouched modules** — apply via batch cherry-pick without per-commit review.
- **Releases that touch Modified modules** get a dedicated tracking issue with:
  - List of conflicting files
  - Assessment of merge difficulty
  - Decision: merge, skip, or defer

### What Happens When Upstream Breaks Anvil

If a rendercv release changes an interface that Anvil depends on:

1. **File an issue** in Anvil's tracker: "Upstream break: rendercv vX.Y changes {module}"
2. **Do NOT auto-fix.** The fix requires understanding both Anvil's and rendercv's intent.
3. **Stay on current fork base** until the fix is reviewed and tested.
4. **If the upstream change improves an interface Anvil wraps**, consider adopting the new interface and updating Anvil's wrapper. This is a design decision, not a mechanical merge.

## Vendoring Strategy

### Directory Structure

```
src/anvilcv/
├── vendor/
│   └── rendercv/          # Vendored rendercv source (from v2.7 tag)
│       ├── __init__.py
│       ├── __main__.py
│       ├── exception.py
│       ├── cli/
│       ├── schema/
│       └── renderer/
├── patches/               # Anvil patches to vendored code
│   ├── README.md          # Documents each patch and why
│   ├── 001-entry-point.patch
│   ├── 002-cli-app.patch
│   └── ...
└── ...                    # Anvil's own code
```

### Patch Documentation

Each modification to vendored rendercv code is tracked as a documented patch:

```markdown
# patches/README.md

## Patch Index

| Patch | File Modified | Purpose | Risk Level |
|-------|--------------|---------|------------|
| 001 | `__init__.py` | Change package name and version | Low |
| 002 | `__main__.py` | Point to Anvil entry point | Low |
| 003 | `cli/app.py` | Replace Typer app, add subcommands | Medium |
| 004 | `cli/entry_point.py` | Change binary name | Low |
| 005 | `schema/models/design/design.py` | Register Anvil themes | Low |
| 006 | `cli/render_command/render_command.py` | Add --variant flag, ATS HTML option | Medium |
| 007 | `cli/render_command/run_rendercv.py` | Add ATS HTML step | Low |
| 008 | `renderer/html.py` | Add ATS HTML generation path | Low |
| 009 | `renderer/path_resolver.py` | Variant-aware path resolution | Low |
| 010 | `renderer/templater/templater.py` | Add render_ats_html function | Low |
```

Risk levels:
- **Low** — Simple additions or renames. Unlikely to conflict with upstream.
- **Medium** — Structural changes. May conflict with upstream refactors.
- **High** — Deep behavioral changes. Will likely conflict with upstream.

## Upstream Communication

Anvil is a hard fork, not an upstream-friendly fork. We do NOT:
- Submit PRs to rendercv for Anvil-specific features
- Expect rendercv to accommodate Anvil's needs
- Maintain a merge-ready branch against upstream

We DO:
- Credit rendercv prominently in README and docs
- Preserve the MIT license
- Report bugs found in vendored code to rendercv upstream (they benefit the community)
- Monitor rendercv's issue tracker for bugs that affect our vendored copy

## Decision Record Template

When evaluating an upstream release, create a decision record:

```markdown
# Upstream Evaluation: rendercv vX.Y

**Date:** YYYY-MM-DD
**Evaluator:** [name]
**Current fork base:** v2.7

## Changes in vX.Y

| Changed File | Module Status in Anvil | Conflicting? |
|-------------|----------------------|-------------|
| ... | Untouched / Extended / Modified | Yes/No |

## Decision

- [ ] Skip this release (no relevant changes)
- [ ] Cherry-pick changes to Untouched modules
- [ ] Merge with manual conflict resolution
- [ ] Defer to next evaluation cycle

## Notes

[Free-form notes on the evaluation]
```

## Metrics

Track these to assess fork health:

| Metric | Target | Frequency |
|--------|--------|-----------|
| Patches behind upstream | < 2 releases | Quarterly |
| Modified module count | Minimize (currently 10) | Each release |
| Compatibility corpus pass rate | 100% | Every CI run |
| Time to evaluate upstream release | < 4 hours | Each evaluation |
