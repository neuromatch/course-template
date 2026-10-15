# Scrollytelling Pages: Design

**Date:** 2026-10-14
**Status:** Draft for review

## Goal

Let any tutorial `.md` opt in to a scrollytelling layout: a pinned stage
(figures, videos, live Python) beside text cards that scroll past. The source
stays a flat, ordinary MyST tutorial, so notebooks, exercises, solutions,
feedback, media and the CI content rules keep working unchanged.

The worked example is **W2D1 Tutorial 2**, a scrolly copy of W2D1 Tutorial 1
(Linear Dynamical Systems), placed next to the original so readers can compare.

## Decisions

- **Flat page + step markers**, not nested containers. Opt in with frontmatter
  `layout: scrolly`. `{step}` markers split the page into steps. All code
  cells, `{nma-*}` directives and exercises stay top level.
- **Browser Python is the kit's own lightweight Pyodide runtime**, not
  JupyterLite/thebe. JupyterLite is hidden on scrolly pages, so each page has
  one runtime.
- **Pre-rendered output.** CI runs scrolly pages headless, and the starting
  outputs are embedded in the page. Readers see real figures without starting
  Python. There are no hand-typed outputs.
- **Interactive demos use Colab form syntax** (`# @param`), not ipywidgets.
  The site shows native sliders and dropdowns. Notebooks get them as
  `widgets.interact`.
- **Notebooks:** a page with `kernelspec` produces a linear notebook as usual.
  A scrolly page without code or `kernelspec` is site-only.
- Pages without `layout: scrolly` are completely unaffected.

## Authoring model

`````markdown
---
title: "Tutorial 2: Linear Dynamical Systems (scrolly)"
layout: scrolly            # read by plugins/ and scripts/, MyST warns "extra key ignored"
kernelspec: {name: python3, display_name: Python 3}
---

```{code-cell} python
:tags: [remove-cell]
# setup: imports, style, helpers, data (open_url under emscripten)
```

:::{step} hero
:kicker: neuromatch academy
:::
# Tutorial 2: *Linear dynamical systems*
Content creators: ...

:::{step}
:section: One dimension
:kicker: Coding Exercise 1
:::
### Forward Euler integration
Fill in the update rule.

```{code-cell} python
def integrate_exponential(a, x0, dt, T):
    ...
    raise NotImplementedError("Student exercise: need to implement simulation")
```

::::{nma-solution}
```python
def integrate_exponential(a, x0, dt, T): ...
```
::::

:::{step}
:kicker: Interactive Demo 1
:::
### Try different α and dt

```{code-cell} python
:tags: [hide-input]
a = -0.5   # @param {type:"slider", min:-2.5, max:1.5, step:0.25}
dt = 0.001 # @param {type:"slider", min:0.001, max:1.0, step:0.001}
x, t = integrate_exponential(a, 1.0, dt, 10)
plt.plot(t, x.real); plt.xlabel("Time (s)"); plt.ylabel("x"); plt.show()
```

:::{nma-explanation}
...
:::

:::{nma-feedback} Forward_Euler_Integration_Interactive_Demo
:::
`````

### Directives

| Directive | Placement | Arg / options |
|---|---|---|
| `{step}` | top level, no body | arg `hero` (optional). `:section:` (label in the progress bar, carries forward), `:kicker:` (small label above the card) |
| `{stage}` | top level, between two step markers, at most one per step | `:style: list`, `:class:`. Body: markdown for the stage (e.g. an objectives list) |

### Splitting a step into stage and card

A step runs from its marker to the next marker (or the end of the page).

- **Stage:** code cells (except `remove-cell`), images/figures (including
  `.mp4`), `{nma-video}`, `{nma-slides}`, and the `{stage}` block.
- **Card:** everything else: prose, math, headings, `{nma-solution}`/
  `{nma-explanation}` links, `{nma-feedback}`.
- If a step has nothing for the stage, the previous stage stays.
- A `hero` step has no card. Its content fills the screen.
- Content before the first marker renders as a normal page header above the
  scrolly section (CI-injected badges land there).

### Code cells on the stage

| Cell | Stage rendering |
|---|---|
| untagged | editable runnable panel (code + output + Run/Reset) |
| `hide-input` | runnable with code collapsed behind "Show code" |
| `remove-input` | output only |
| `remove-cell` | invisible. Runs before the first visible cell |
| has `# @param` lines | panel gets sliders/dropdowns. Changes rerun the cell |

`# @param` forms supported (Colab syntax, so the code is valid Python as is):

```python
a = -0.5     # @param {type:"slider", min:-2.5, max:1.5, step:0.25}
option = 1   # @param [1, 2, 3, 4]
```

## Runtime (site)

Built from the sketch kit. It lives in `plugins/scrolly/` and is registered in
`myst.yml` next to `plugins/nma.mjs`.

- `plugins/scrolly/scrolly.mjs`: the `{step}`/`{stage}` directives emit
  markers. A document-stage transform (only when frontmatter says
  `layout: scrolly`) walks the top-level blocks, groups them by marker, and
  rebuilds the tree as `.scrolly > .scrolly-stage(views) + .scrolly-steps(cards)`.
  Each code-cell `block` is replaced by a runnable anywidget whose model is
  `{code, mode, params, cellIndex, initialOutput, solution?}`.
- `plugins/scrolly/engine.mjs`: scroll tracking (IntersectionObserver),
  activates views, progress bar + section label, "Enable Python" pill, and
  plays/pauses `<video>` in the active view.
- `plugins/scrolly/runnable.mjs`: shared page-level Pyodide.
  - **Notebook semantics:** running cell *k* first silently runs any earlier
    cells that haven't run yet, in order, in one namespace. So the
    `remove-cell` setup and the exercise functions are defined automatically.
  - **Exercises:** if an earlier cell still has an uncommented
    `raise NotImplementedError`, its `{nma-solution}` code runs in its place.
    This is the same "hidden, not secret" rule as the existing run-all
    fallback. The solution code is embedded in the widget model.
  - **Packages:** `loadPackagesFromImports` on each cell's code, plus
    `micropip` for anything listed in setup cells. No `:packages:` option.
  - **Pyodide URL:** `nma.scrolly.pyodide_url` in `myst.yml`, read with
    `readNmaConfig()`.
- `plugins/scrolly/scrolly.css`: layout (two columns ≥900px, stacked below,
  full-bleed section), loaded through `_static/custom.css`.
- JupyterLite power button: disabled per page if MyST allows it, otherwise
  hidden with CSS scoped to scrolly pages.

## Pre-rendering (CI)

`scripts/nma_scrolly.py --render`, run in `publish-book.yml` before
`--prepare-site` and `myst build`:

1. For each `layout: scrolly` page with `kernelspec`, take its generated
   **instructor** notebook (solutions filled in) from `convert_to_notebooks.py`.
2. Execute it with nbclient (CPython, `requirements.txt` deps).
   `# @param` cells run with their default values.
3. Write `_build/scrolly/<Day>/<stem>.json`:
   `{sha256(student cell source): {stdout, png[]}}`.
4. The plugin reads that file at build time and sets `initialOutput`.
   Exercise cells get no initial output.

Failure modes:

- A cell that raises fails CI with file and cell number.
- A missing render file (e.g. local `myst start`) is a warning. Panels show
  "Run to see output".

## Notebooks

`scripts/nma_scrolly.py` also provides a pre-jupytext pass, called from
`convert_to_notebooks.py`:

- Removes `{step}` markers. A `:kicker:` becomes an italic line. `hero` adds
  nothing.
- Unwraps `{stage}` blocks into plain markdown.
- Rewrites cells with `# @param` lines into `widgets.interact`
  (`FloatSlider`/`IntSlider`/`Dropdown`). It adds the ipywidgets import to
  the setup if missing.
- Everything else (media, solutions, feedback, badges) goes through the
  existing pipeline unchanged.

The student and instructor notebooks for Tutorial 2 therefore look like normal
NMA notebooks.

## Validation (CI, both modes)

Python (`nma_scrolly.py`) and JS (`scrolly.mjs`) apply the same rules:

- `{step}`/`{stage}` only on pages with `layout: scrolly`, top level, no body
  on `{step}`, at most one `{stage}` per step, unknown options are errors.
- Malformed `# @param` lines on scrolly pages are errors.
- `layout: scrolly` with no `{step}` is an error.
- The `--prepare-site` run-all fallback cell is not injected on scrolly pages
  (the runtime does the substitution itself).

Shared fixtures in `tests/fixtures/scrolly/` drive pytest and `node --test`,
following the feedback-config pattern.

## Worked example: W2D1 Tutorial 2

`tutorials/W2D1_Examples/W2D1_Tutorial2.md` is a scrolly copy of Tutorial 1,
with the same prose, math, exercises, videos and explanations. Its feedback
prefix is the filename default `W2D1_T2`, so its feedback stays separate from
Tutorial 1's. It is added to the `myst.yml` TOC and to the schedule in
`chapter_intro.md`.

Rough step outline (about 22 steps):

1. hero: title and credits
2. Objectives (stage: `{stage}` list + `{nma-slides}`)
3. Section 1: video 1 (stage), feedback (card)
4. 1-D ODE, analytic solution (stage: `remove-input` plot)
5. Coding Exercise 1: Euler (stage: exercise cell) + solution link
6. Euler vs. analytic result (stage: `remove-input` plot)
7. Interactive Demo 1: α, dt sliders + explanation
8. Section 2: video 2
9. Interactive Demo 2: real/imaginary sliders + explanation
10. Section 3: video 3, 2-D system math
11. Coding Exercise 3: trajectories + solution link
12. Trajectory result
13. Demo 3A: varying A (dropdown `option = 1 # @param [1, 2, 3, 4]`)
14. Demo 3B: varying x0 (dropdown)
15. Section 4: stream plots (`hide-input`) + Think! 4 explanation
16. hero: summary

Tutorial 1 is not modified.

## Risks to check first (spikes)

1. A document-stage transform can replace MyST code-cell `block`/`output`
   nodes with anywidget nodes, and the theme renders them in custom
   containers.
2. JupyterLite can be turned off per page (frontmatter), or hidden with CSS.
3. jupytext keeps the `{step}`/`{stage}` directives as markdown (they are
   stripped before jupytext anyway, so this is a fallback concern only).
4. `{figure}` with `.mp4` renders `<video>` in the book theme.
5. Pyodide loads from the configured CDN on the custom domain (CORS).

## Out of scope (later)

- Scroll-scrubbed video, Vega-Lite stages, SVG layer reveal.
- Running the CI pre-render inside Pyodide/Node.
- Converting other existing tutorials.
