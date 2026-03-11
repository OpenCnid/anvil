# Patch Index

Modifications to vendored rendercv v2.7 code are tracked here.

| Patch | File Modified | Purpose | Risk Level |
|-------|--------------|---------|------------|
| P-001 | `vendor/rendercv/__init__.py` | Package identity: version from anvilcv, description updated | **Low** |
| P-002 | `vendor/rendercv/__main__.py` | Redirect `python -m` to Anvil entry point | **Low** |
| P-003 | `vendor/rendercv/cli/entry_point.py` | Redirect CLI entry point to Anvil | **Low** |
| P-004 | `vendor/rendercv/cli/app.py` | Replace Typer app with Anvil's; vendored command auto-discovery preserved | **Medium** |

## Extended Files

Files where new functionality was appended without altering existing code.

| Patch | File Extended | Purpose | Risk Level |
|-------|--------------|---------|------------|
| E-001 | `vendor/rendercv/cli/render_command/render_command.py` | Extended: Added `--no-ats-html` CLI flag to skip ATS HTML generation | **Low** |
| E-002 | `vendor/rendercv/cli/render_command/run_rendercv.py` | Extended: Added ATS HTML generation step after standard HTML in the render pipeline | **Low** |
| E-003 | `vendor/rendercv/renderer/html.py` | Extended: Added `generate_ats_html()` function for ATS HTML file generation with path derivation | **Low** |
| E-004 | `vendor/rendercv/renderer/templater/templater.py` | Extended: Added `render_ats_html()` bridge function that converts RenderCVModel to dict for ATS renderer, including social_networks extraction | **Low** |
| E-005 | `schema/models/design/built_in_design.py` | Extended: Imported DevforgeTheme and added to BuiltInDesign discriminated union for theme registration | **Low** |

Risk levels:
- **Low** — Simple additions or renames. Unlikely to conflict with upstream.
- **Medium** — Structural changes. May conflict with upstream refactors.
- **High** — Deep behavioral changes. Will likely conflict with upstream.
