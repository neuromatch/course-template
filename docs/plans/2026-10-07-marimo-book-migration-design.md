# Marimo + marimo-book Migration Design

**Date:** 2026-10-07
**Status:** Approved design, ready for implementation planning
**Branch:** `marimo-template`

## Goal

Replace the MyST/JupyterLite toolchain with marimo notebooks published by
[marimo-book](https://marimobook.org) (v0.1.x, alpha). Tutorials become marimo
`.py` notebooks, which are the single source of truth. Most of the book is
interactive in the browser through WebAssembly (Pyodide). Compute-intensive
pages ship pre-rendered static output.

This also fixes the main open problem from
`2026-09-29-editable-code-cells-findings.md`: in MyST, students cannot edit
code cells in the browser. marimo-book's workbench `edit` view gives them a
full marimo editor running in Pyodide, and their edits persist in IndexedDB.

## Decisions

| Topic | Decision |
|---|---|
| Scope | Full replacement of MyST. No coexistence. |
| Default page rendering | `mode: static`, executed in CI at build time, so pages load fast with no Pyodide download |
| In-browser execution | Workbench `views: [read, edit]`. Students click Edit to run and modify code in Pyodide. |
| Read-view interactivity | `precompute.enabled: true`, so discrete `mo.ui` sliders, dropdowns and switches work without a kernel |
| Compute-heavy pages | `mode: cached` with `views: [read]`. Authors run `marimo-book render` locally and commit `_rendered/`. |
| Dependencies | `dependencies.mode: env` with a uv venv. `marimo-book sync-deps` writes PEP 723 blocks into notebooks. Heavy deps go in a local-only `heavy` group. |
| Colab/Kaggle | Dropped. The launch buttons are molab, GitHub and download `.py`. |
| Solutions | Hidden cell that renders `mo.accordion` with the solution code as markdown |
| Existing content | Rewrite W1D1–W1D3 as marimo/marimo-book meta-tutorials. Port W2D1 LDS. Add a cached-mode demo. |

Why the workbench instead of `defaults.mode: wasm`: `mode: wasm` pages are
reactive but their code is read-only. Combining wasm pages with the workbench
runs two Pyodide kernels at once, and the marimo-book docs advise against
that. Static read plus workbench edit loads fast and still gives students full
editing.

## Architecture

```
book.yml                     # replaces myst.yml (metadata, TOC, defaults)
pyproject.toml / uv.lock     # replaces requirements.txt; groups: build (default), heavy (local-only)
CNAME                        # template.neuromatch.io, auto-copied to _site/
content/
  intro.md
  W1D1_GettingStarted/       # chapter_intro.md, W1D1_Tutorial{1..3}.py, W1D1_Bonus.py, further_reading.md
  W1D2_InteractiveContent/
  W1D3_PublishingAndCI/
  W2D1_Examples/             # W2D1_Tutorial1.py (LDS port), W2D1_Tutorial2_Heavy.py (cached demo)
  projects/README.md
_rendered/                   # committed outputs for mode: cached pages only
_wheels/                     # kept: vibecheck/datatops wheels served via raw.githubusercontent.com
images/
.github/workflows/deploy.yml # single workflow
```

**Removed:** `myst.yml`, `requirements.txt`, `scripts/convert_to_notebooks.py`,
`generate-notebooks.yml`, `publish-book.yml`, `notebooks-branch`, and
`tutorials/` (renamed to `content/`). Remove `build-pyodide-wheels.yml` unless
we need to rebuild the wheels.

**Gitignored:** `_site/`, `_site_src/`, `.marimo_book_cache/`, `__marimo__/`
(unless a persistent cache is committed on purpose).

### book.yml (key parts)

```yaml
title: Neuromatch Course Template
repo: https://github.com/neuromatch/course-template
url: https://template.neuromatch.io
license: CC-BY-4.0

launch_buttons: {molab: true, github: true, download: true}
precompute: {enabled: true}
dependencies: {mode: env}

defaults:
  mode: static
  views: [read, edit]
  open_in: read
  suppress_warnings: true

toc:
  - file: content/intro.md
  - section: "Day 1: Getting Started"
    children:
      - file: content/W1D1_GettingStarted/chapter_intro.md
      - file: content/W1D1_GettingStarted/W1D1_Tutorial1.py
      # ...
  - section: "Day 4: Real Content Example"
    children:
      - file: content/W2D1_Examples/W2D1_Tutorial1.py
      - file: content/W2D1_Examples/W2D1_Tutorial2_Heavy.py
        mode: cached
        views: [read]
```

## Authoring Conventions

| MyST today | marimo equivalent |
|---|---|
| `kernelspec` frontmatter | Any `.py` page is executable; `.md` pages are static |
| `hide-input` (infrastructure, videos, plot helpers) | `@app.cell(hide_code=True)` |
| `remove-cell` (setup) | First cell (`import marimo as mo` plus imports), auto-hidden by `hide_first_code_cell` |
| Exercise with `raise NotImplementedError` | Normal visible cell. Downstream cells catch `NotImplementedError` and show a `mo.callout("Complete the exercise above", kind="warn")` instead of crashing. |
| Solution (`# to_remove solution`) | `hide_code=True` cell that renders `mo.accordion({"Solution": mo.md("```python ...```")})`. Expected output comes from a hidden reference implementation. |
| `@widgets.interact` / ipywidgets | `mo.ui.slider(steps=[...])` and similar. Use 50 or fewer discrete values so precompute covers them. |
| Videos (`IFrame` / `YouTubeVideo`) | `mo.Html(iframe)` / `mo.ui.tabs` for YouTube and Bilibili, in a `hide_code=True` cell |
| `<details>`, admonitions | `mo.accordion` / `mo.callout`; in `.md` pages use `!!!` / `???` |
| KaTeX workarounds | Not needed. marimo-book uses MathJax 3 (`align` and similar work). |
| micropip setup cell | Not needed for PyPI packages (the workbench reads PEP 723). For non-PyPI wheels, use a guarded `if sys.platform == "emscripten": await micropip.install(<raw.githubusercontent URL>)`. |

**Exercises must never raise during export.** Static mode with `--strict` fails
the build on any cell error, which is why the guard pattern is required.

**Feedback widget:** vibecheck's `DatatopsContentReviewContainer` is built on
ipywidgets, which marimo does not support. For now, replace it with an
`mo.md` link to the feedback form. Porting it to anywidget is a follow-up.

## Build, CI, Deploy

### Local

```bash
uv sync                                  # build deps
uv run marimo-book serve                 # live reload at :8000
uv run marimo-book build --strict
uv sync --group heavy && uv run marimo-book render   # only for cached pages; commit _rendered/
uv run marimo-book sync-deps             # after changing imports
```

### `.github/workflows/deploy.yml`

Triggers: push to `main`, pull requests (build only), `workflow_dispatch`.

1. Checkout, `astral-sh/setup-uv`, `uv sync` (no `heavy` group)
2. `actions/cache` for `.marimo_book_cache/`, keyed on `uv.lock` + `book.yml`
3. `uv run marimo-book check`
4. `uv run marimo-book sync-deps --check`: PEP 723 blocks in sync
5. `uv run marimo-book render --check`: `_rendered/` not stale; runs nothing
6. `uv run marimo-book build --strict`
7. On `main` only: upload `_site/` and deploy with `actions/deploy-pages@v4`

### Size

The workbench ships about 27 MB of marimo frontend assets, which must be served
from our own origin. Pyodide (about 30 MB, cached by the browser) only loads
when a student opens Edit.

## Content Plan

- **W1D1 Getting Started**
  - T1: marimo notebook anatomy (cells, reactivity, `mo.md`)
  - T2: `book.yml` and TOC
  - T3: figures, math, callouts
  - Bonus: layout elements
- **W1D2 Interactive Content**
  - T1: `mo.ui` widgets and precompute
  - T2: workbench edit view and the exercise/solution pattern
  - T3: static vs workbench vs cached
  - Bonus: anywidget
- **W1D3 Publishing and CI**
  - T1: deploy workflow
  - T2: dependencies and `sync-deps`
  - T3: cached mode for heavy content
  - Bonus: scaling to a multi-week course
- **W2D1 Examples**
  - T1: full LDS port, keeping all prose, math, videos, exercises and solutions
  - T2: small heavy demo in `cached` mode (long simulation or small torch model, deps in the `heavy` group)

## Verification (Definition of Done)

- `marimo-book build --strict` passes locally and in CI.
- Every exercise page renders in read view with guard callouts and no errors.
- Deployed site, checked by hand:
  - Read view loads with no Pyodide request.
  - Edit boots the workbench; numpy, scipy and matplotlib import; an exercise can be edited and run; edits survive a reload.
  - Discrete sliders respond in read view (precompute).
  - The cached page shows its committed outputs.
- `sync-deps --check` and `render --check` pass, and each fails when deliberately broken (checked once).
- `template.neuromatch.io` serves the new site.

## Migration Order

1. Scaffold the toolchain (`pyproject.toml`, `book.yml`, `content/intro.md`), with a local build passing
2. Port W2D1 Tutorial 1 (highest risk: widgets, videos, solve_ivp, exercises)
3. Add the cached-mode demo (W2D1 Tutorial 2)
4. Rewrite W1D1–W1D3
5. Replace CI workflows with `deploy.yml`
6. Rewrite `AGENTS.md` and `README.md` for the marimo conventions
7. Delete MyST artifacts
8. Merge `marimo-template` into `main`

## Risks

- **marimo-book is alpha (0.1.x).** Pin `marimo-book>=0.1.48,<0.2`.
- **ipywidgets is unsupported.** Affects the feedback widget and any `@widgets.interact`; covered by the conventions above.
- **Custom wheel URLs in PEP 723 / `extras` are undocumented.** Fallback is the guarded micropip cell, served from `raw.githubusercontent.com` for CORS.
- **Precompute limits** (50 values per widget, 200 combinations per page, 60 s per page). Pages that exceed them fall back to static widgets with a warning. Design sliders within the limits, or tune `max_*`.
- **The workbench is unavailable on phones** (narrower than about 720 px). Phone users get the read view only.

## Out of Scope

Colab/Kaggle export, PR preview deploys, porting vibecheck to anywidget, PDF
export, marimo-grader integration.
