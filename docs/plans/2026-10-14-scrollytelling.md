# Scrollytelling Pages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Opt-in `layout: scrolly` tutorial pages (pinned stage + scrolling cards, live Pyodide panels, CI pre-rendered output) and a scrolly copy of W2D1 Tutorial 1 as W2D1 Tutorial 2.

**Architecture:** The page stays a flat MyST tutorial. `{step}`/`{stage}` are markers. A document-stage transform in `plugins/scrolly/scrolly.mjs` regroups the top-level nodes into `.scrolly > .scrolly-stage + .scrolly-steps` and turns code cells into `runnable.mjs` anywidgets. `scripts/nma_scrolly.py` validates pages, flattens them for jupytext, and pre-renders outputs with nbclient.

**Tech Stack:** mystmd 1.11 plugins (ESM), anywidget nodes, Pyodide 314.0.7 (jsDelivr), Python 3 + jupytext + nbclient, pytest, node --test.

Design: `docs/plans/2026-10-14-scrollytelling-design.md`.

## Spike results (done)

- At the document stage, markers appear as top-level nodes inside `block`s in document order. Code cells are `block{kind:'notebook-code', data:{tags}} > code{value} + outputs`.
- Replacing the tree with divs + `anywidget{esm,css,model,class}` renders. Leading-`/` asset paths are hashed into `/build/`.
- `block.class = 'col-screen'` gives full width (the theme's `grid-column: screen`), so no JS margin hacks.
- `.mp4` images render as `<video>`. The asset is copied.
- A frontmatter `jupyter: false` is ignored, so the power button is hidden with CSS (`body:has(.scrolly) .myst-jp-nb-toolbar-power`).
- Plugin order follows `myst.yml`.
- Pyodide `v314.0.7` on jsDelivr sends `access-control-allow-origin: *`.
- Cell key: `sha256(normalised code)[:16]`, where normalised means `\r\n` -> `\n`, trailing spaces stripped per line, outer blank lines stripped. Shared fixture `tests/fixtures/scrolly/cell_keys.json`.

## Shared contracts (Python and JS must agree)

- `layout: scrolly` in the frontmatter (plain `layout:` line).
- `{step}`: optional arg `hero`, options `section`, `kicker`, no body. `{stage}`: options `style`, `class`, markdown body.
- `# @param` grammar (one per line, assignment form):
  - `name = <number>  # @param {type:"slider", min:N, max:N, step:N}`
  - `name = <literal>  # @param [lit, lit, ...]`
  - Parsed result is `{name, kind:'slider'|'dropdown', value, min, max, step, options}`. Fixture: `tests/fixtures/scrolly/params.json`.
- Render file: `_build/scrolly/<relDir>/<stem>.json` = `{"<key>": {"stdout": str, "images": [base64 png], "error": null}}`.
- Config: `nma.scrolly.pyodide_url` in `myst.yml`.

## Tasks

### Task 1: Python core (`scripts/nma_scrolly.py`, `tests/test_nma_scrolly.py`)
- `is_scrolly(text)`, `find_markers(text)` (reuses `nma_solutions.find_blocks` with kinds `("step","stage")`), `cell_key(code)`, `parse_params(code)`.
- `validate(text)`:
  - Markers only on scrolly pages, top level only.
  - `{step}` has no body, its arg is empty or `hero`, and it has no unknown options.
  - At most one `{stage}` per step, and none before the first step.
  - The page has at least one `{step}`.
  - Malformed `# @param` lines are errors.
- TDD against both fixtures. Commit.

### Task 2: Notebook flattening + interact rewrite
- `flatten_for_notebook(text)`: `{step}` -> nothing, or `*kicker*` when a kicker is set. `{stage}` -> its body.
- `params_to_interact(code)`: param lines are removed from the body, which is wrapped in `@widgets.interact(name=widgets.FloatSlider|IntSlider|Dropdown(...))` + `def _demo(<names>):`. Adds `import ipywidgets as widgets`.
- Hook into `convert_to_notebooks.py`: flatten into a temp `.md` before jupytext, then rewrite `# @param` code cells in the notebook.
- `validate_content` calls `nma_scrolly.validate`. `prepare_site_md` skips the run-all fallback on scrolly pages.
- Tests: the existing suite stays green, plus new flatten/interact tests. Commit.

### Task 3: Pre-render (`--render`)
- `nma_scrolly.py --render`: for each scrolly kernelspec page, build the instructor notebook in a temp dir (reuse `convert_to_notebooks` functions), drop solution-link-free cells as is, and execute with nbclient (cwd = page dir, timeout 300s).
- Map each executed code cell back to its source cell (student source key; for an exercise cell the key of the exercise source maps to no output). Write the render file. Exit 1 with page and cell number on error.
- Add `nbclient`, `nbformat` and `scipy` to `requirements.txt`.
- Test with a tiny fixture page (print + matplotlib figure). Commit.

### Task 4: Plugin (`plugins/scrolly/scrolly.mjs`, `tests/js/scrolly.test.mjs`)
- Directives `step`/`stage` emit `scrollyStep`/`scrollyStage` nodes.
- Exported pure functions: `cellKey`, `parseParams`, `isScrolly`, `buildScrolly(tree, {renders, solutions, config})`.
- Transform: only on scrolly pages. Flatten the top-level blocks, split stage/card per the design, and put `hero` content on the stage.
  - Code cells -> anywidget `{code, mode, params, index, initial, fallback}`. Each exercise carries the code of the `{nma-solution}` that follows it, read from the source file via a small fence scan.
  - Wrap in `block{class:'col-screen'}`.
  - Engine anywidget first, with model `{n, map, hero, sections, pyodideUrl}`.
- Node tests on the fixtures + `buildScrolly` with a hand-built tree. Commit.

### Task 5: Browser runtime (`engine.mjs`, `runnable.mjs`, `scrolly.css`)
- Adapted from the sketch.
  - Engine: IntersectionObserver, active view, progress, section label, Python pill, play/pause `<video>` in the active view. No full-bleed JS.
  - Runnable: one shared runtime on `window.NMA_PY`. `run(index)` first runs earlier unrun cells (registry by index), substituting `fallback` for unfinished exercises. Imports load via `loadPackagesFromImports`. Sliders and dropdowns come from params; changes rerun after 180ms. Initial output comes from `initial`.
- `scrolly.css` gets the layout, card and hero styles, and hides the power button. It is imported from `_static/custom.css`.
- Register the plugin and `nma.scrolly.pyodide_url` in `myst.yml`. Unit-test pure helpers (`highlight`, `paramsPrelude`). Commit.

### Task 6: W2D1 Tutorial 2
- Copy Tutorial 1 into scrolly form (about 16 steps, see the design outline). Demos use `# @param`. A `remove-cell` setup runs imports, style and plotting helpers.
- Update the TOC and the chapter_intro schedule. Commit.

### Task 7: CI wiring
- `publish-book.yml`: run `uv run python scripts/nma_scrolly.py --render` before `--prepare-site`, and add `scripts/**` to its push paths if missing. `generate-notebooks.yml` is unchanged (it already installs requirements and runs pytest).
- Commit.

### Task 8: Documentation (how to use scrolly pages in the template)
Authors learn the template from the book itself, so the main guide is a book page, backed by AGENTS.md for agents.

- **New how-to page** `tutorials/W1D2_InteractiveContent/W1D2_Tutorial6.md`, "Tutorial 6: Scrollytelling Pages". **The page is itself a scrolly page** (`layout: scrolly` + `kernelspec`), so it teaches each feature by using it:
  - Each step's **card** explains one feature and shows its syntax in a ```` ````markdown ```` fence. Fenced examples are literal text: the Python scanner treats non-directive fences as opaque, and MyST makes them `code` nodes, so the `{step}`/`{code-cell}` lines inside them are never treated as real markers or cells. Add a test for this in both `test_nma_scrolly.py` and `scrolly.test.mjs`.
  - Each step's **stage** shows the feature working: a hero step, a `{stage}` `:style: list`, an untagged editable cell, a `hide-input` cell, a `remove-input` figure, a `# @param` slider and dropdown demo, a tiny real exercise with `{nma-solution}` (to show the fallback when running ahead), an `{nma-explanation}`, an `{nma-feedback}`, and an `{nma-video}` on the stage.
  - Keep the Python small and Pyodide-safe (numpy and matplotlib only, no data files), so `--render` is fast and the page works in the browser.
  - Because it has `kernelspec`, it also gets a generated notebook. That notebook is the "what the Colab version looks like" example for section 10.
  - Write it after Task 6, and use it in Task 9 to check every feature end to end.

  Sections (one or more steps each):
  1. What a scrolly page is, and when to use it (a narrative walkthrough of figures and demos) or not (long reference material, heavy exercises).
  2. Turning a page on: `layout: scrolly`, then `{step}` markers. A minimal three-step example.
  3. `{step}` options: `hero`, `:section:`, `:kicker:`. `{stage}` with `:style: list`.
  4. What goes on the stage vs the card (table from the design), and "the stage carries forward".
  5. Code cells: the tag table (untagged / `hide-input` / `remove-input` / `remove-cell`), the shared namespace, and "earlier cells run first".
  6. Interactive demos with `# @param` (slider + dropdown syntax). Show the before/after of turning a `@widgets.interact` demo into `# @param`, and say that notebooks get `widgets.interact` automatically.
  7. Exercises, solutions, explanations, videos and feedback work unchanged (link to Tutorials 4 and 5), plus the solution fallback when running ahead.
  8. Browser Python: the "Enable Python" pill, first load size, which packages work (Pyodide), loading data with `open_url`, and the `nma.scrolly.pyodide_url` setting.
  9. Pre-rendered outputs: what `--render` does, that a raising cell fails CI, and how to preview locally (`uv run python scripts/nma_scrolly.py --render && uv run myst start`). Missing renders show "Run to see output".
  10. Notebooks: what the Colab/Kaggle version looks like (linear, markers removed).
  11. Converting an existing tutorial: a checklist, pointing at W2D1 Tutorial 1 → Tutorial 2 as the worked example.
  12. CI errors you may see, and their fixes (the `validate()` messages).
- Register it in the `myst.yml` TOC after W1D2 Tutorial 5, and add a row to the W1D2 `chapter_intro.md` schedule (`Tutorial 6 | Scrollytelling pages | 20 min`) and a line to its learning objectives.
- `W1D2_InteractiveContent/further_reading.md`: links to the MyST plugin docs, the anywidget spec, and Pyodide.
- `W1D3_PublishingAndCI/W1D3_Tutorial1.md`: add the `--render` step to the pipeline description of `publish-book.yml`.
- `W2D1_Examples/chapter_intro.md`: describe Tutorial 2 as the scrolly version of Tutorial 1 and invite readers to compare them.
- **AGENTS.md:**
  - Architecture tree: `plugins/scrolly/`, `scripts/nma_scrolly.py`, `tests/fixtures/scrolly/`.
  - Key files: entries for both.
  - New "Scrollytelling pages" convention section: syntax, tag table, `# @param`, the rules shared by Python and JS (`cellKey`, param grammar, render file path), "never hand-write outputs".
  - Content rules: add the scrolly validation rules.
  - Build & CI: `--render` and local preview.
  - Conversion checklist: a pointer for scrolly conversions.
- **README.md:** one line under "For course authors" pointing to the scrollytelling tutorial.
- Commit: `docs: explain scrollytelling pages in the template`.

### Task 9: Verification
- `uv run pytest -q`, `node --test tests/js/*.test.mjs`, `convert_to_notebooks.py --dry-run` and a real run (inspect the Tutorial 2 student and instructor notebooks), `nma_scrolly.py --render`, `convert_to_notebooks.py --prepare-site` on a scratch copy, `myst build --html` (no ⛔), then `git checkout -- tutorials/`.
- Load the built site in chromium (`/usr/bin/chromium --headless --screenshot`) at 1280 and 400 widths, on Tutorial 2 and on the new W1D2 Tutorial 6 page. Confirm that the stage switches on scroll, pre-rendered figures appear, and on Tutorial 6 every demonstrated feature works (sliders rerun, the exercise fallback runs, feedback posts). Inspect the Tutorial 6 student and instructor notebooks too.
- Commit any fixes.
