# AGENTS.md

Context for AI agents working on this repository.

## Project Overview

Neuromatch course template built with MyST (Markedly Structured Text). MyST `.md` files in `tutorials/` are the single source of truth. Jupyter notebooks (`.ipynb`) are generated artifacts, never authored directly. The rendered book deploys to GitHub Pages via CI.

## Architecture

```
myst.yml                    # Single config: metadata, TOC, JupyterLite, site theme, nma: settings
tutorials/
  intro.md                  # Landing page
  W{week}D{day}_{Topic}/    # One directory per day
    chapter_intro.md         # Day overview, learning objectives, schedule table
    W{w}D{d}_Tutorial1.md   # Tutorial pages (kernelspec required if they contain code)
    W{w}D{d}_Tutorial2.md
    W{w}D{d}_Bonus.md       # Open-ended bonus
    further_reading.md       # Static links page
scripts/
  convert_to_notebooks.py   # Converts .md -> .ipynb, injects Colab/Kaggle badges
  nma_media.py              # Validates {nma-video}/{nma-slides}, expands them into notebook cells
  nma_solutions.py          # Validates {nma-solution}/{nma-explanation}, builds student/instructor notebooks
  nma_feedback.py           # Validates {nma-feedback} and the nma: settings, writes feedback cells
  nma_scrolly.py            # Scrolly pages: validates, flattens for notebooks, --render pre-renders outputs
  nma_cells.py              # `runtime:` frontmatter (browser | colab): runtime_of + validation
plugins/
  nma.mjs                   # MyST plugin: media -> static embeds, solutions -> links, feedback -> widget
  nma-feedback.mjs          # Browser-side feedback widget (anywidget ESM), posts to datatops
  scrolly/
    scrolly.mjs             # MyST plugin: {step}/{stage} markers, stage/card layout on `layout: scrolly` pages
    engine.mjs              # Browser: scroll tracking, active stage view, progress bar, Python pill
    runnable.mjs            # Browser: runnable code panels on one shared Pyodide runtime
    scrolly.css             # Page layout (attached to the engine widget, copied into <head>)
    runnable.css            # Panel styles (inside each widget's shadow root)
  cells/
    cells.mjs               # MyST plugin: editable cells on browser pages, Colab banner on `runtime: colab` pages
    src/model.mjs           # Pure helpers (modes, fallback marker, runtimeOf), unit-tested
    src/runtime.mjs         # Browser: one thebe-lite kernel per page, run queue, restart
    src/{editor,panel,runtime-widget}.mjs   # CodeMirror 6 editor, panel widget, hidden manifest widget
    cells.css / page.css    # Panel styles (shadow root) / page rules (copied into <head>)
    dist/                   # GENERATED esbuild bundles, committed (npm run build in plugins/cells)
tests/                       # pytest for scripts/; tests/js/ is node --test for plugins/
  e2e/                       # Playwright smoke test of the built site (needs NMA_E2E_URL)
  fixtures/scrolly/          # cell_keys.json, params.json: shared by Python and JS tests
_wheels/                     # Pre-built .whl files for Pyodide (CORS-friendly hosting)
_static/
  custom.css                 # Custom CSS for the book theme
projects/
  README.md                  # Project booklet placeholder
notebooks/                   # Generated files (gitignored, lives on notebooks-branch):
                             #   <Day>/<T>.ipynb, <Day>/instructor/<T>.ipynb, <Day>/solutions/*
.github/workflows/
  generate-notebooks.yml     # Converts tutorials, pushes to notebooks-branch
  publish-book.yml           # Builds MyST book, deploys to GitHub Pages
  build-pyodide-wheels.yml   # Builds wheels for packages missing them on PyPI
```

### Key files

- **`myst.yml`** -- the only config file. Contains project metadata, hand-authored TOC, JupyterLite settings (`project.jupyter.lite: true`), site theme, and the top-level `nma:` block (Neuromatch settings read by `plugins/` and `scripts/`, not by MyST, which logs `extra key ignored: nma`). There is no `_toc.yml` or `_config.yml`.
- **`scripts/convert_to_notebooks.py`** -- reads `project.github` from `myst.yml` to generate fork-friendly badge URLs. Default mode writes the student and instructor notebooks and the solution files. `--prepare-site` (CI-only, alias `--inject-md-badges`) adds badges and the run-all fallback cell to `.md` pages. Both modes first enforce the content rules below. Idempotent.
- **`plugins/nma.mjs`** -- MyST JavaScript plugin (registered under `project.plugins` in `myst.yml`). Renders `{nma-video}` as a YouTube/Bilibili/OSF tab set of iframes and `{nma-slides}` as an OSF iframe plus download link, at build time with no kernel. Renders `{nma-solution}`/`{nma-explanation}` as "Click for solution/explanation" links to the solution files on `notebooks-branch`.
- **`scripts/nma_media.py`** -- the Python side of the same directives. It validates them and, after jupytext, replaces each one with a hidden NMA `# @title Video …` / `# @title Tutorial slides` code cell in the generated notebook. Its URL templates must stay in sync with `plugins/nma.mjs`.
- **`scripts/nma_solutions.py`** -- the Python side of `{nma-solution}`/`{nma-explanation}`. It validates them, splits each generated notebook into student and instructor versions, writes the solution files, and builds the site's run-all fallback cell. Its file naming and URL rules must stay in sync with `plugins/nma.mjs`.
- **`scripts/nma_feedback.py`** / **`plugins/nma-feedback.mjs`** -- `{nma-feedback}`. The Python side validates the directive and the `nma:` block and writes the notebook feedback cells. The JS widget posts to datatops from the browser. `read_nma_block()` (Python) and `readNmaConfig()` (in `nma.mjs`) are two copies of the same line-based reader and must stay in sync. Shared fixtures in `tests/fixtures/nma_config/` test both.
- **`scripts/nma_scrolly.py`** / **`plugins/scrolly/`** -- scrollytelling pages (`layout: scrolly`). The Python side validates pages, flattens them before jupytext (`flatten_for_notebook`), turns `# @param` cells into `widgets.interact` (`params_to_interact`), and pre-renders outputs with nbclient (`--render`). The plugin lays the page out and turns code cells into runnable Pyodide panels. `is_scrolly`/`isScrolly`, `cell_key`/`cellKey` and `parse_params`/`parseParams` are two copies of the same rules, tested against `tests/fixtures/scrolly/`.
- **`scripts/nma_cells.py`** / **`plugins/cells/`** -- editable cells (see "Editable cells"). `runtime_of`/`runtimeOf` are two copies of the same rule, tested against `tests/fixtures/cells/runtime.json`. `NO_FALLBACK_MARKER` in `nma_solutions.py` and `model.mjs` must match.
- **`requirements.txt`** -- Python dependencies: mystmd (pinned: the panels use its bundled thebe 0.5.0 API), jupytext, numpy, matplotlib, playwright (e2e), etc.
- **`.nvmrc`** -- Node.js version (22). MyST requires Node >= 20.

## Key Conventions

### Frontmatter reference

| Key | Values | Read by | Effect |
|---|---|---|---|
| `title` | string | MyST | Page title (always set it). |
| `kernelspec` | `name: python3`, `display_name: Python 3` | MyST, scripts, plugins | Makes the page executable: editable cells, generated notebooks, badges. Required if the page has a `{code-cell}`. |
| `runtime` | `browser` (default), `colab` | `nma_cells.py`, `cells.mjs` | `colab` = read-only code plus a Colab/Kaggle banner, no fallback cell. Not with `layout: scrolly`. |
| `layout` | `scrolly` | `nma_scrolly.py`, `scrolly.mjs` | Scrollytelling page. Pair with `site: {hide_outline: true}`. |
| `feedback_prefix` | string | `nma_feedback.py`, `nma.mjs` | Overrides the prefix of `{nma-feedback}` ids. |

MyST logs `extra key ignored` for `runtime`, `layout` and `feedback_prefix`; that is expected. The user-facing version of this table is `tutorials/W1D1_GettingStarted/W1D1_Tutorial4.md`: keep both in sync when a key is added.

### Executable vs static pages

A page with `kernelspec` in its YAML frontmatter is executable:

```yaml
---
title: "Tutorial 1: Some Topic"
kernelspec:
  name: python3
  display_name: Python 3
---
```

This means:
- every code cell becomes an editable, runnable panel (see "Editable cells"), unless the page sets `runtime: colab`
- `convert_to_notebooks.py` generates a `.ipynb` from it
- CI injects Colab/Kaggle badges

A page without `kernelspec` is static (chapter intros, further reading, bonus pages without code).

### Content rules (enforced by CI)

`convert_to_notebooks.py` validates these rules before doing anything, in both modes, and exits non-zero on any violation:

- **No `.ipynb` in `tutorials/`.** All content is MyST `.md`. Convert incoming notebooks once (see "Converting .ipynb to MyST .md") and commit only the `.md`.
- **Pages with code need `kernelspec`.** A `.md` file with a top-level `{code-cell}` must declare `kernelspec`. Code-cells shown as examples inside another fenced block don't count.
- **Exercises need solutions.** Every top-level exercise code cell (an uncommented `raise NotImplementedError` line) must be directly followed by an `{nma-solution}`, and every `{nma-solution}` must directly follow an exercise. No `# to_remove` markers may be left in code cells. Solution bodies must be a single ```` ```python ```` fence, explanations can't be empty, and neither directive may be nested or take options.
- **Media directives must be valid.** Every top-level `{nma-video}` needs a title and at least one of `:youtube:`/`:bilibili:`/`:osf:`. Every `{nma-slides}` needs an OSF id. Unknown options, body text and unclosed blocks are errors, reported with file and line.
- **Feedback uses the directive.** `{nma-feedback}` takes a section name (`[A-Za-z0-9_]+`, unique per page), at the top level, with no options or body. No code cell may call `content_review(`, import `vibecheck`, or be an "Import feedback gadget" cell. If any page uses `{nma-feedback}`, `myst.yml` must have `nma.feedback.{url,project,user_key}`, and the `nma:` block must be plain `key: value` lines with string values.

- **`runtime` must be valid.** Frontmatter `runtime:` is `browser` (default) or `colab`, and `colab` can't be combined with `layout: scrolly`.
- **Scrolly pages must be valid.** `{step}`/`{stage}` only on pages with `layout: scrolly`, at the top level. `{step}` takes no argument or `hero`, only `:section:`/`:kicker:`, and no body. At most one `{stage}` per step (options `:style: list`, `:class:`), none before the first step. A `layout: scrolly` page needs at least one `{step}`. On scrolly pages, every `# @param` line must parse (see "Scrollytelling pages").

There is no Binder, JupyterHub, or remote-kernel support. Code runs in the browser (editable cells on JupyterLite's kernel), and Colab/Kaggle (via the generated notebooks) is the fallback for anything Pyodide can't run.

### Editable cells

Every visible code cell on a **browser page** (has `kernelspec`, not `layout: scrolly`, not `runtime: colab`) is a CodeMirror 6 editor with a **▶ Run** button (Shift-Enter / Ctrl-Enter too). It runs on the JupyterLite kernel that MyST already ships (thebe-lite, Pyodide 0.27), one kernel per page. The JupyterLite power button is hidden site-wide in `_static/custom.css`. Keep `project.jupyter.lite: true`, since MyST only emits the thebe assets with it.

- **Colab pages.** A heavy tutorial adds `runtime: colab` to its frontmatter (MyST warns `extra key ignored: runtime`, expected). It shows read-only code and an "important" admonition, *Do this tutorial in Colab*, that links to Colab and Kaggle. No fallback cell is added. `tutorials/W2D1_Examples/W2D1_Tutorial3.md` is an example.
- **How a Run works.** Like a notebook: earlier cells that haven't run go first, then the target. An earlier *unfinished* exercise runs its `{nma-solution}` through the kernel-side fallback cell from `--prepare-site`. The cell the student explicitly runs gets a trailing `# nma-no-fallback` line, which switches the fallback off for that cell, so a partly edited exercise shows `NotImplementedError` and never the solution. Running stops at the first earlier cell that fails.
- **Modes by tag.** none = editor + output, `hide-input`/`hide-cell` = editor behind "Show code", `remove-input` = output only (Run button), `remove-cell` = no panel, runs as an earlier cell. Exercises get an accent colour and the label "Exercise · fill in, then run".
- **Edits live in memory only**, per page (Reset restores the original). Changing page disposes the kernel and starts a fresh one when you come back. **Restart** starts a new kernel session.
- **Styling.** CSS variables with light and dark defaults (`html.dark`/`html.light`), overridable from `_static/custom.css`: `--nma-cell-{bg,fg}-{light,dark}`, `--nma-cell-border`, `--nma-cell-radius`, `--nma-cell-accent`, `--nma-cell-exercise-accent`, `--nma-cell-bar-{bg,fg}-{light,dark}`, `--nma-cell-gutter-{bg,fg}-{light,dark}`, `--nma-cell-active-line-{light,dark}`, `--nma-cell-font-family`, `--nma-cell-font-size-value`, `--nma-tok-{keyword,string,number,comment,function,definition}-{light,dark}`. Example: `:root { --nma-cell-accent-value: #2a9d8f; --nma-tok-keyword-light: #b5179e; } html.dark { --nma-tok-keyword-dark: #f72585; }`.
- **Outside services** (students' browsers must reach them): `cdn.jsdelivr.net` (Pyodide 0.27, widget JS), `cdnjs.cloudflare.com` (`require.js`, MathJax, font-awesome), `pypi.org`/`files.pythonhosted.org` (`micropip`). Scrolly pages load their own, newer Pyodide, so package availability can differ.
- **Bundles.** `plugins/cells/dist/*.mjs` are generated and committed. After changing `plugins/cells/src/`, run `cd plugins/cells && npm ci && npm run build` and commit `dist/`. CI fails if it is stale. Browser code must never use root-absolute URLs (forks deploy under `github.io/<repo>/`): derive them from `import.meta.url`.
- **Browser smoke test.** `uv run playwright install chromium`, build the site as in "Local preview" (with `--prepare-site`, then `git checkout -- tutorials/`), serve `_build/html` (`python3 -m http.server 8765`), then `NMA_E2E_URL=http://localhost:8765 uv run pytest -q tests/e2e`. If `cdnjs` is blocked, also set `NMA_E2E_REQUIREJS=<path to require.js>` (see `tests/e2e/conftest.py`).

### Badges

Never add or commit badge HTML in `.md` files. The `.md` sources on `main` are badge-free. Badges are added at build time in two places:
- **Generated notebooks**: `generate-notebooks.yml` inserts a badge cell at position 0 of each `.ipynb`.
- **Rendered site pages**: `publish-book.yml` runs `convert_to_notebooks.py --prepare-site` right before `myst build`, on CI's throwaway checkout. The result is never committed.

Every page with `kernelspec` gets badges automatically, so local `myst start` previews show no badges.

### Videos and slides

Never write video or slide players as code cells. Use the directives:

```markdown
:::{nma-video} Video 1: Linear Dynamical Systems
:youtube: 87z6OR7-DBI
:bilibili: BV1up4y1S7wj
:::

:::{nma-slides} snv4m
:::
```

- On the site, `plugins/nma.mjs` renders them as static iframes (tabs for multiple hosts), so they show without starting JupyterLite.
- In generated notebooks, `scripts/nma_media.py` replaces them with the standard hidden NMA code cells (ipywidgets Tab / OSF IFrame).
- Options: `nma-video` takes `:youtube:`, `:bilibili:`, `:osf:` (at least one). `nma-slides` takes an optional `:title:` (default "Tutorial slides").
- Put them at the top level of the page (not nested in other directives), with options only and no body.
- Adding a host means updating `VIDEO_SOURCES` in both files.

### Feedback

Never write feedback cells (`content_review(...)`, the vibecheck "Import feedback gadget" cell) by hand. Use the directive:

```markdown
:::{nma-feedback} Linear_Dynamical_Systems_Video
:::
```

- The section id sent is `<prefix>_<name>`. The prefix is the frontmatter `feedback_prefix:` if set (MyST warns `extra key ignored`, which is expected), otherwise derived from the filename: `W2D1_Tutorial1` -> `W2D1_T1`, any other stem is used as is. Set `feedback_prefix` when converting an NMA notebook so its ids stay the same.
- Where responses go is set once in `myst.yml`:

  ```yaml
  nma:
    feedback:
      url: https://pmyvdlilci.execute-api.us-east-1.amazonaws.com/klab
      project: neuromatch_cn
      user_key: y1x3mpx5   # write-only, published in every notebook; not a secret
  ```

- **Site:** `plugins/nma.mjs` turns each directive into MyST's `anywidget` node backed by `plugins/nma-feedback.mjs`. It renders 🙂/😐/🙁 with no kernel and POSTs `{button_name, feedback, section_id, timestamp_utc}` to `<url>/api/v1/projects/<project>` with header `X-User-Key`, the same request vibecheck makes.
- **Notebooks:** each directive becomes a hidden `# @title Submit your feedback` / `content_review(f"{feedback_prefix}_<name>")` cell, and one hidden "Import feedback gadget" cell (`%pip install vibecheck datatops`, `content_review`, `feedback_prefix`) is added at the top. Notebooks only run on Colab/Kaggle/local Jupyter, so it has no Pyodide branch.

### Exercises, solutions and explanations

Never write solutions or explanations as code cells (the old `# to_remove solution` / `# to_remove explanation` convention, which CI now rejects). Use the directives:

`````markdown
```{code-cell} python
def f(x):
  raise NotImplementedError("Student exercise: implement f")
```

::::{nma-solution}
```python
def f(x):
  return 2 * x
```
::::

:::{nma-explanation}
Markdown answer to a discussion question, math allowed: $a < 0$.
:::
`````

- The exercise is a normal untagged `{code-cell}`. The `{nma-solution}` goes directly after it, with only blank lines in between. Its outer fence needs more colons than the inner ```` ```python ```` fence.
- `{nma-explanation}` stands alone, usually after an interactive demo or a "Think!" question.
- Both go at the top level of the page, with no argument and no options.
- **Site:** a *Click for solution/explanation* link to `notebooks/<Day>/solutions/<T>_Solution_<n>.py` / `<T>_Explanation_<n>.md` on `notebooks-branch`, where `n` counts each directive type from the top of the page. The answer isn't shown on the page.
- **Student notebook:** the same link as a markdown cell. **Instructor notebook** (`notebooks/<Day>/instructor/`): the solution as a code cell starting with `# Solution`, and the explanation as markdown under **Explanation**.
- **Run-all fallback (site only):** `--prepare-site` adds a hidden `remove-cell` setup cell to pages with exercises. It registers an IPython input transformer: while a cell still has an uncommented `raise NotImplementedError` line, the matching reference solution runs instead (exact match, else the closest by `difflib` ≥ 0.6), so "Run all" in JupyterLite doesn't stop. The solutions are hidden, not secret.

### Scrollytelling pages

Opt in with `layout: scrolly` in the frontmatter, plus `site: {hide_outline: true}` (MyST warns `extra key ignored: layout`, which is expected). The page stays a flat tutorial. `{step}` markers split it into steps, and each step is a **card** (prose) plus a pinned **stage**. The how-to page is `tutorials/W1D2_InteractiveContent/W1D2_Tutorial6.md` (itself a scrolly page), and `tutorials/W2D1_Examples/W2D1_Tutorial2.md` is a full example.

```markdown
:::{step} hero
:kicker: neuromatch academy
:::
# Title

:::{step}
:section: One dimension
:kicker: Coding Exercise 1
:::
Card text. Code cells, images, figures, {nma-video}/{nma-slides} after the
marker go on the stage; prose, math, solution links and {nma-feedback} on the card.

:::{stage}
:style: list
1. Stage-only markdown
:::
```

- The section is placed between the book theme's TOC sidebar and "On this page" outline (`.scrolly-col` in `scrolly.css`), and its layout uses container queries on its own width: stage beside the cards from 760px (`WIDE` in `engine.mjs`), stacked below that. Scrolly pages should set frontmatter `site: hide_outline: true` to give the section the outline's space, but not `hide_toc`: with it the theme leaves the TOC out of the page entirely (no sidebar, and the small-screen menu opens empty), so readers can't move to another page mid-story.
- Engine (HUD), stage and steps share one grid cell (`grid-area: 1 / 1`), not negative margins. A sticky element with `margin-bottom: -height` keeps sticking a screen past its parent and covered the footer prev/next links (regression test in `tests/js/scrolly.test.mjs`).
- A step with nothing for the stage keeps the previous stage. A `hero` step has no card. Content before the first `{step}` is a normal page header.
- Code cells on the stage: untagged = editable panel, `hide-input` = code collapsed, `remove-input` = output only, `remove-cell` = invisible (runs before the first visible cell).
- Panels share one Pyodide runtime (`nma.scrolly.pyodide_url` in `myst.yml`). Running a cell first runs earlier unrun cells. An earlier unfinished exercise runs its `{nma-solution}` instead. JupyterLite's power button is hidden on these pages.
- Interactive demos use Colab form syntax, one top-level assignment per line: `a = -0.5  # @param {type:"slider", min:-2.5, max:1.5, step:0.25}` (`step` defaults to 1) or `option = 1  # @param [1, 2, 3, 4]` (the default must be in the list). Never use `@widgets.interact` on scrolly pages. Notebooks get `widgets.interact` automatically.
- **Never hand-write outputs.** `scripts/nma_scrolly.py --render` runs each scrolly page's instructor notebook (exercise cells removed, `# @param` at defaults, cwd = page dir) and writes `_build/scrolly/<relDir>/<stem>.json` = `{cell_key: {stdout, images, error}}`. A raising cell fails CI with `file:line`. Exercise cells get no starting output.
- Rules shared by Python and JS (keep in sync, fixtures in `tests/fixtures/scrolly/`): `cell_key` = first 16 hex chars of sha256 of the code with CRLF -> LF, trailing spaces/tabs stripped per line, outer blank lines stripped. The `# @param` grammar above, parsed to `{name, kind, value, min, max, step, options}`. The render file path.
- Notebooks: markers are removed (a `:kicker:` becomes an italic line), `{stage}` blocks are unwrapped, and `# @param` cells become `widgets.interact`. Avoid "on the right"/"on the stage" in card text, since the notebook shows it too.

### Code cell tags

```markdown
```{code-cell} python
# Regular cell -- fully visible, editable and runnable on the page
```

```{code-cell} python
:tags: [hide-input]
# Code hidden behind toggle, output visible. Used for:
# - Infrastructure (plotting functions, figure settings)
# - Interactive widgets (@widgets.interact)
```

```{code-cell} python
:tags: [remove-cell]
# Completely hidden. Used for setup code (e.g., micropip installs)
```
```

Exercise cells (containing `raise NotImplementedError`) must have NO tags so students can see and edit them.

### LaTeX

MyST uses KaTeX, not MathJax. Common incompatibilities:

| Does NOT work (LaTeX) | Use instead (KaTeX) |
|---|---|
| `\begin{eqnarray}` | `\begin{aligned}` wrapped in `$$` |
| `\begin{array} & a & b` | `\begin{bmatrix} a & b` |
| `\\\\` (double backslash) in `eqnarray` | `\\` in `aligned` |

Always test math rendering with `myst build --html`.

## Build & CI

### Local preview

```bash
# Requires Node >= 20 (use nvm if needed)
export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh" && nvm use 22
uv run myst start          # Dev server at localhost:3000
uv run myst build --html   # Full build to _build/html/
```

For scrolly pages, run `uv run python scripts/nma_scrolly.py --render` first so the panels show real outputs (otherwise they show "Run to see output").

### Notebook conversion (local, optional)

```bash
uv run python scripts/convert_to_notebooks.py           # Convert all
uv run python scripts/convert_to_notebooks.py --dry-run  # Preview only
uv run pytest -q                                          # Tests for scripts/
node --test tests/js/*.test.mjs                           # Tests for plugins/
```

This writes only to `notebooks/` (gitignored) and never modifies `.md` files. The separate `--prepare-site` mode edits `.md` files in place and is meant for CI only. If you run it locally, revert with `git checkout -- tutorials/`.

### CI pipelines

1. **`generate-notebooks.yml`** -- triggers on push to `main` when `tutorials/`, `scripts/`, `tests/`, `myst.yml`, or `requirements.txt` change. Runs `pytest`, converts `.md` -> `.ipynb` (expanding media directives into code cells), pushes to `notebooks-branch`.
2. **`publish-book.yml`** -- triggers after `generate-notebooks.yml` completes or on push to `main` (including changes under `plugins/` and `scripts/`). Checks that `plugins/cells/dist/` is up to date, runs `node --test tests/js/*.test.mjs`, then `nma_scrolly.py --render` (pre-renders scrolly pages), then `convert_to_notebooks.py --prepare-site` (badges plus the exercise fallback cell) on its throwaway checkout, then builds the MyST book, runs the browser smoke test (`tests/e2e`) against it and deploys to GitHub Pages.
3. **`build-pyodide-wheels.yml`** -- manual trigger (`workflow_dispatch`). Builds pure-Python wheels for packages that lack them on PyPI, uploads as GitHub Release assets.

### Adding a new day

1. Create `tutorials/W{w}D{d}_{Topic}/` with `chapter_intro.md`, tutorial `.md` files, `further_reading.md`
2. Add the TOC entry in `myst.yml` under `project.toc`. Make `- file: tutorials/W{w}D{d}_{Topic}/chapter_intro.md` the top-level entry and list the tutorials under it as `children`. Don't wrap it in a `title:` group, because that makes the day appear twice in the sidebar.
3. Validate: `python3 -c "import yaml; yaml.safe_load(open('myst.yml'))"`

## Pyodide / JupyterLite

### Bundled packages

numpy, matplotlib, scipy, pandas, altair -- available in Pyodide out of the box.

### Packages needing micropip

ipywidgets -- install via micropip in a setup cell. (Feedback needs nothing: the site widget is plain JS.)

### Wheel hosting (CORS)

Micropip fetches wheels from URLs in the browser. **GitHub Releases URLs are NOT CORS-friendly** -- they block `Access-Control-Allow-Origin`. Use `raw.githubusercontent.com` instead, which sends proper CORS headers.

Pre-built wheels live in `_wheels/` and are served via:
```
https://raw.githubusercontent.com/neuromatch/course-template/main/_wheels/<package>.whl
```

This is a temporary workaround. Once upstream maintainers publish wheels to PyPI, remove the URL workaround and install by package name.

### No sockets: downloading files

Pyodide can't open sockets, so `urllib.request` / `http.client` (and anything built on them, such as `plt.style.use(<url>)` or `pd.read_csv(<url>)`) fail in the browser with `OSError: [Errno 23] Host is unreachable`. Under `sys.platform == "emscripten"`, fetch with `pyodide.http.open_url(url)` (synchronous) or `await pyodide.http.pyfetch(url)`, write the result to a local file, and use that path. `requests` works as is because Pyodide patches it. The host must send CORS headers (`raw.githubusercontent.com` does).

### Setup cell pattern

```python
import sys
if sys.platform == "emscripten":
    import micropip
    await micropip.install(["ipywidgets"])
```

For a package served from `_wheels/`, add `f"https://raw.githubusercontent.com/<org>/<repo>/main/_wheels/<file>.whl"` to the list.

## Converting .ipynb to MyST .md

### Cell mapping

| Notebook cell type | MyST equivalent |
|---|---|
| `"cell_type": "markdown"` | Raw markdown content |
| `"cell_type": "code"` | `` ```{code-cell} python `` |
| Badge cell (position 0) | Omit -- CI injects badges |
| `cellView: "form"` / `# @title` | `:tags: [hide-input]` |
| `# to_remove solution` | `{nma-solution}` directly after the exercise cell (drop the marker line) |
| `# to_remove explanation` | `{nma-explanation}` (turn the docstring into Markdown) |
| `raise NotImplementedError` (exercise) | No tags (students must see/edit) |
| `# @markdown` / `@widgets.interact` | `:tags: [hide-input]` |
| `# @title Submit your feedback` (`content_review(f"{feedback_prefix}_X")`) | `{nma-feedback} X` |
| `# @title Import feedback gadget` | Omit -- generated. Copy its `feedback_prefix` into the frontmatter if it differs from the filename default |
| Video cell (`# @title Video …`, `video_ids = [...]`) | `{nma-video}` directive (copy the ids) |
| Slides cell (`# @title Tutorial slides`, `link_id = …`) | `{nma-slides}` directive (the `link_id`) |

### Frontmatter

Replace all notebook metadata with clean MyST frontmatter:

```yaml
---
title: "Tutorial N: Title Here"
kernelspec:
  name: python3
  display_name: Python 3
---
```

### Checklist for conversion

1. Strip badge cell (position 0)
2. Add clean frontmatter with `kernelspec`
3. Add Pyodide setup cell if needed (micropip installs)
4. Convert all code cells to `{code-cell}` directives with appropriate tags
5. Replace video and slides cells with `{nma-video}`/`{nma-slides}`, and feedback cells with `{nma-feedback}` (drop the gadget cell, set `feedback_prefix` if needed)
6. Replace `# to_remove solution` cells with `{nma-solution}` and `# to_remove explanation` cells with `{nma-explanation}`
7. Normalize LaTeX for KaTeX compatibility
8. Preserve all prose, math, `<details>` blocks, HTML as-is
9. Add day directory, `chapter_intro.md`, `further_reading.md`
10. Register in `myst.yml` TOC
11. Test: `myst build --html` -- check for `⛔` errors

For a scrollytelling version, follow the "Converting an existing tutorial" checklist in W1D2 Tutorial 6 (merge setup into one `remove-cell`, add `{step}` markers, rewrite demos with `# @param`, run `--render`).
