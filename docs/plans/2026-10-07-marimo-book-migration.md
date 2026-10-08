# Marimo + marimo-book Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the MyST/JupyterLite course template with marimo `.py` notebooks published by marimo-book. Pages render statically by default, students edit in the in-browser workbench (WASM), and compute-heavy pages use committed `cached` output.

**Architecture:** `book.yml` replaces `myst.yml`. Tutorials live in `content/` as marimo notebooks (the single source of truth); static prose stays `.md`. CI runs `marimo-book build --strict` (static pages execute at build time) and deploys `_site/` to GitHub Pages. `mode: cached` pages are rendered locally and committed under `_rendered/`. Design: `docs/plans/2026-10-07-marimo-book-migration-design.md`.

**Tech Stack:** marimo, marimo-book `>=0.1.48,<0.2` (Material for MkDocs shell), uv, pytest, numpy/scipy/matplotlib, Pyodide (workbench), GitHub Actions + Pages.

---

## Ground rules for the implementer

- Work on branch `marimo-template` (it exists and equals `main`). Use a worktree if you prefer: @using-git-worktrees.
- Toolchain commands always run through uv: `uv run marimo-book ...`, `uv run pytest ...`.
- **marimo rules you will hit constantly:**
  1. A global name can be defined in **only one cell**. Reused scratch names (`T`, `dt`, `x0`, `A`, `fig`) must be prefixed `_` (cell-local) or given unique names.
  2. A cell's displayed output is its **last expression**. Don't use `plt.show()`; end the cell with `fig` or `plt.gca()`.
  3. A hidden-code cell is `@app.cell(hide_code=True)`.
  4. Author notebooks with `uv run marimo edit content/...py`, or edit the file directly and then run `uv run marimo check content/...py`.
- **Exercise/solution pattern (used everywhere):** see Task 6. Exercises must never raise during export, because `build --strict` fails on cell errors.
- Commit after every task. Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`), matching repo history.

---

### Task 0: Commit the design doc and switch branch

**Step 1:**
```bash
git checkout marimo-template
git add docs/plans/2026-10-07-marimo-book-migration-design.md docs/plans/2026-10-07-marimo-book-migration.md
git commit -m "docs: add marimo-book migration design and plan"
```
Expected: one commit on `marimo-template`.

---

### Task 1: Inspect the marimo-book scaffold (research, no repo changes)

Goal: copy real conventions from the tool instead of guessing them.

**Step 1:**
```bash
cd /tmp/opencode && uvx --from 'marimo-book>=0.1.48,<0.2' marimo-book new scaffold
```
**Step 2:** Read `scaffold/book.yml`, `scaffold/content/*`, `scaffold/.github/workflows/deploy.yml` and `scaffold/pyproject.toml` (if present). Note:
- the exact notebook header (`app = marimo.App(...)`, PEP 723 block format)
- the deploy workflow steps and the actions versions it uses
- the `.gitignore` entries it generates

**Step 3:** Run `cd scaffold && uvx --from 'marimo-book>=0.1.48,<0.2' marimo-book build` and confirm `_site/index.html` exists.

**Step 4:** If any later task in this plan disagrees with the scaffold (key names, workflow shape), **follow the scaffold** and note the change in the commit message. Nothing to commit for this task.

---

### Task 2: Python project and ignore rules

**Files:**
- Create: `pyproject.toml`
- Modify: `.gitignore`

**Step 1:** Create `pyproject.toml`:
```toml
[project]
name = "neuromatch-course-template"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "marimo-book>=0.1.48,<0.2",
  "marimo",
  "numpy",
  "scipy",
  "matplotlib",
]

[dependency-groups]
dev = ["pytest"]
heavy = ["torch"]   # local-only; used by mode: cached pages, never installed in CI

[tool.uv]
default-groups = ["dev"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```
**Step 2:** Append to `.gitignore`:
```
_site/
_site_src/
.marimo_book_cache/
__marimo__/
```
**Step 3:** `uv lock && uv sync`. Expected: creates `uv.lock`, exit 0.

**Step 4:** `uv run marimo-book --help`. Expected: lists `new build serve check render sync-deps clean`.

**Step 5:**
```bash
git add pyproject.toml uv.lock .gitignore
git commit -m "chore: add uv project for marimo-book toolchain"
```

---

### Task 3: Notebook smoke-test harness (TDD foundation)

Every content notebook must run headless without errors. marimo notebooks are plain Python, and `app.run()` executes all cells and returns `(outputs, defs)`.

**Files:**
- Create: `tests/conftest.py`, `tests/test_notebooks.py`

**Step 1: Write the test**

`tests/conftest.py`:
```python
import importlib.util
import os
import pathlib

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
HEAVY = {"W2D1_Examples/W2D1_Tutorial2_Heavy.py"}  # cached pages: skipped unless heavy deps installed


def notebook_paths():
    return sorted(
        p for p in CONTENT.rglob("*.py")
        if not p.name.startswith("_") and "__marimo__" not in p.parts
    )


def run_notebook(path: pathlib.Path):
    """Import a marimo notebook and run all cells; return defs dict."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _outputs, defs = mod.app.run()
    return defs


@pytest.fixture
def run():
    return run_notebook
```

`tests/test_notebooks.py`:
```python
import pytest

from conftest import CONTENT, HEAVY, notebook_paths, run_notebook


@pytest.mark.parametrize(
    "path", notebook_paths(), ids=lambda p: str(p.relative_to(CONTENT))
)
def test_notebook_runs_without_error(path):
    if str(path.relative_to(CONTENT)) in HEAVY:
        pytest.importorskip("torch")
    run_notebook(path)


def test_there_are_notebooks():
    assert notebook_paths(), "no marimo notebooks found under content/"
```

**Step 2: Run it and confirm it fails**

`uv run pytest -v`. Expected: `test_there_are_notebooks` FAILS (no `content/` yet).

**Step 3:** Leave it failing. Task 5 makes it pass.

**Step 4:**
```bash
git add tests/
git commit -m "test: add headless smoke test for marimo notebooks"
```

> If `app.run()` does not return `(outputs, defs)` in the installed marimo, check `uv run python -c "import marimo, inspect; print(inspect.signature(marimo.App.run))"` and adapt `run_notebook`.

---

### Task 4: book.yml, landing page and projects page

**Files:**
- Create: `book.yml`, `content/intro.md`, `content/projects/README.md`
- Keep: `CNAME` (already contains `template.neuromatch.io`)

**Step 1:** Create `book.yml`. The TOC lists only pages that exist so far; later tasks add entries.
```yaml
title: Neuromatch Course Template
description: A template for building Neuromatch courses with marimo and marimo-book.
authors:
  - name: Neuromatch
repo: https://github.com/neuromatch/course-template
branch: main
url: https://template.neuromatch.io
license: CC-BY-4.0
copyright: "Code: BSD-3-Clause · Content: CC-BY-4.0"

logo_placement: sidebar

launch_buttons:
  molab: true
  github: true
  download: true

dependencies:
  mode: env

precompute:
  enabled: true
  max_seconds_per_page: 300

defaults:
  mode: static
  views: [read, edit]
  open_in: read
  suppress_warnings: true
  hide_first_code_cell: true

toc:
  - file: content/intro.md
  - file: content/projects/README.md
```
**Step 2:** Port `tutorials/intro.md` to `content/intro.md`:
- Drop the MyST frontmatter; use a `# Title` heading.
- Convert MyST directives (`:::{note}`, `{admonition}`) to Material syntax (`!!! note`).
- Replace JupyterLite/Colab wording with: "Every tutorial page has an **Edit** button that opens the notebook in your browser (no install). You can also open it in molab or download the `.py` and run `marimo edit`."

Copy `projects/README.md` to `content/projects/README.md` with the same conversions.

**Step 3:** `uv run marimo-book check`. Expected: exit 0.

**Step 4:** `uv run marimo-book build --strict`. Expected: exit 0, `_site/index.html` and `_site/CNAME` exist (`ls _site/CNAME`).

**Step 5:** `uv run marimo-book serve`, open http://127.0.0.1:8000, eyeball it, then stop the server.

**Step 6:**
```bash
git add book.yml content/
git commit -m "feat: scaffold marimo-book config and landing page"
```

---

### Task 5: W2D1 port, part 1: skeleton, header, setup and plot helpers

This is the highest-risk page, so it goes first. Source: `tutorials/W2D1_Examples/W2D1_Tutorial1.md` (1010 lines).

**Files:**
- Create: `content/W2D1_Examples/W2D1_Tutorial1.py`
- Create: `content/W2D1_Examples/chapter_intro.md` (port of `tutorials/W2D1_Examples/chapter_intro.md`)
- Create: `content/W2D1_Examples/further_reading.md` (port)
- Modify: `book.yml` (TOC)

**Step 1:** Create the notebook skeleton. Use the header format from the Task 1 scaffold; the layout looks like this:
```python
import marimo

__generated_with = "<filled by marimo>"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.integrate import solve_ivp
    return mo, np, plt, solve_ivp


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Tutorial 1: Linear dynamical systems

    **Week 2, Day 3: Linear Systems**
    ...  (header, credits, Tutorial Objectives verbatim from source lines 22-52)
    """)
    return


if __name__ == "__main__":
    app.run()
```
Notes:
- Math: keep `\begin{equation}...\end{equation}` as is; MathJax renders it.
- Use raw strings `r"""` for all `mo.md` with LaTeX.

**Step 2:** Figure settings cell (hidden). It replaces the URL-based `plt.style.use`, which needs network sockets that Pyodide lacks:
```python
@app.cell(hide_code=True)
def _(plt):
    import logging
    logging.getLogger("matplotlib.font_manager").disabled = True
    try:
        plt.style.use("https://raw.githubusercontent.com/NeuromatchAcademy/course-content/main/nma.mplstyle")
    except Exception:
        plt.rcParams.update({"figure.figsize": (8, 6), "axes.spines.top": False,
                             "axes.spines.right": False, "font.size": 12})
    return
```

**Step 3:** Shared helper cell (hidden) with the video and slides helpers, defined once and used by every section:
```python
@app.cell(hide_code=True)
def _(mo):
    def video_tabs(youtube_id, bilibili_id, w=854, h=480):
        yt = f'<iframe width="{w}" height="{h}" src="https://www.youtube.com/embed/{youtube_id}?rel=0" allowfullscreen></iframe>'
        bb = f'<iframe width="{w}" height="{h}" src="https://player.bilibili.com/player.html?bvid={bilibili_id}&page=1&autoplay=0" allowfullscreen></iframe>'
        return mo.ui.tabs({
            "YouTube": mo.vstack([mo.Html(yt), mo.md(f"Video available at https://youtube.com/watch?v={youtube_id}")]),
            "Bilibili": mo.vstack([mo.Html(bb), mo.md(f"Video available at https://www.bilibili.com/video/{bilibili_id}")]),
        })

    FEEDBACK_URL = None  # TODO: course team supplies the form URL; None hides the link

    def feedback_link(section):
        # vibecheck is ipywidgets-based (unsupported in marimo); link-out until an anywidget port exists
        if not FEEDBACK_URL:
            return mo.md("")
        return mo.md(f"*Feedback on this section ({section}):* [submit here]({FEEDBACK_URL}?section={section})")

    def exercise_pending(name):
        return mo.callout(mo.md(f"Complete **{name}** above to see this output."), kind="warn")
    return exercise_pending, feedback_link, video_tabs
```
> Ask the course team for the feedback form URL. Until it is set, `feedback_link` renders nothing.

**Step 4:** Slides cell (hidden): `mo.Html` iframe for the OSF render URL (source lines 56-61), plus the download link as `mo.md`.

**Step 5:** Plotting helpers cell (hidden): copy `plot_trajectory`, `plot_streamplot` and `plot_specific_example_stream_plots` verbatim from source lines 107-265, then:
- Replace each trailing `plt.show()` with `return fig` (or `plt.gcf()`), so callers can make it the last expression.
- Return the three helpers from the cell.

**Step 6:** Add the TOC entry to `book.yml`:
```yaml
  - section: "Day 4: Real Content Example"
    children:
      - file: content/W2D1_Examples/chapter_intro.md
      - file: content/W2D1_Examples/W2D1_Tutorial1.py
      - file: content/W2D1_Examples/further_reading.md
```
Port the two `.md` pages the same way as in Task 4.

**Step 7:** `uv run marimo check content/W2D1_Examples/W2D1_Tutorial1.py && uv run pytest -v`. Expected: both pass (`test_there_are_notebooks` now passes).

**Step 8:** `uv run marimo-book build --strict`. Expected: exit 0.

**Step 9:**
```bash
git add content/W2D1_Examples book.yml
git commit -m "feat(W2D1): port tutorial skeleton, setup and helpers to marimo"
```

---

### Task 6: W2D1 port, part 2: Section 1 (exercise/solution pattern and Demo 1)

The reusable exercise pattern is defined here. Every later exercise copies it.

**Files:**
- Modify: `content/W2D1_Examples/W2D1_Tutorial1.py`
- Create: `tests/test_w2d1_solutions.py`

**Step 1: Write the failing solution test**
```python
import numpy as np
import pathlib
from conftest import run_notebook

NB = pathlib.Path(__file__).resolve().parents[1] / "content/W2D1_Examples/W2D1_Tutorial1.py"


def test_ref_integrate_exponential_matches_analytic():
    defs = run_notebook(NB)
    f = defs["ref_integrate_exponential"]
    x, t = f(-0.5, 1.0, 0.001, 10)
    np.testing.assert_allclose(x.real, np.exp(-0.5 * t), atol=1e-3)


def test_student_stub_raises():
    defs = run_notebook(NB)
    import pytest
    with pytest.raises(NotImplementedError):
        defs["integrate_exponential"](-0.5, 1.0, 0.001, 10)
```
Run `uv run pytest tests/test_w2d1_solutions.py -v`. Expected: FAIL with `KeyError: 'ref_integrate_exponential'`.

**Step 2:** Add the Section 1 cells in source order:
1. `mo.md` heading "Section 1: One-dimensional Differential Equations"
2. Hidden cell: `video_tabs("87z6OR7-DBI", "BV1up4y1S7wj")`
3. `feedback_link("Linear_Dynamical_Systems_Video")`
4. `mo.md` prose. The `<details>` "text recap" becomes `mo.accordion({"Click here for text recap of video": mo.md(r"...")})`.
5. `mo.md` "Coding Exercise 1" prose

**Step 3:** Exercise cell (visible, **no** `hide_code`). It defines only the stub, copied verbatim from source lines 372-406:
```python
@app.cell
def _(np):
    def integrate_exponential(a, x0, dt, T):
        """...docstring verbatim..."""
        t = np.arange(0, T, dt)
        x = np.zeros_like(t, dtype=complex)
        x[0] = x0
        for k in range(1, len(t)):
            ###################################################################
            ## Fill out the following then remove
            raise NotImplementedError("Student exercise: need to implement simulation")
            ###################################################################
            xdot = ...
            x[k] = ...
        return x, t
    return (integrate_exponential,)
```

**Step 4:** Guarded "try it" cell (visible). Scratch names get a `_` prefix so later cells can reuse them:
```python
@app.cell
def _(exercise_pending, integrate_exponential, plt):
    _a, _T, _dt, _x0 = -0.5, 10, 0.001, 1.0
    try:
        _x, _t = integrate_exponential(_a, _x0, _dt, _T)
        _fig, _ax = plt.subplots()
        _ax.plot(_t, _x.real); _ax.set_xlabel("Time (s)"); _ax.set_ylabel("x")
        _out = _fig
    except NotImplementedError:
        _out = exercise_pending("Coding Exercise 1")
    _out
    return
```

**Step 5:** Solution cell (hidden). One string feeds both the displayed solution and the reference implementation:
```python
@app.cell(hide_code=True)
def _(mo, np, plt):
    _src = '''
def integrate_exponential(a, x0, dt, T):
    t = np.arange(0, T, dt)
    x = np.zeros_like(t, dtype=complex)
    x[0] = x0
    for k in range(1, len(t)):
        xdot = (a * x[k-1])
        x[k] = x[k-1] + xdot * dt
    return x, t
'''
    _ns = {"np": np}
    exec(_src, _ns)
    ref_integrate_exponential = _ns["integrate_exponential"]

    _x, _t = ref_integrate_exponential(-0.5, 1.0, 0.001, 10)
    with plt.xkcd():
        _fig, _ax = plt.subplots()
        _ax.plot(_t, _x.real); _ax.set_xlabel("Time (s)"); _ax.set_ylabel("x")
    mo.accordion({"Solution": mo.vstack([mo.md(f"```python\n{_src.strip()}\n```"), _fig])})
    return (ref_integrate_exponential,)
```
Include the full original docstring in `_src` (source lines 428-456) so the shown solution matches NMA.

**Step 6:** Interactive Demo 1:
- **Discrete steps** keep it inside the precompute limits: 17 × 10 = 170 combinations, under the cap of 200.
- Demos use `ref_integrate_exponential`, so they work in read view whether or not the exercise is done.

```python
@app.cell(hide_code=True)
def _(mo):
    demo1_a = mo.ui.slider(steps=[round(-2.5 + 0.25 * i, 2) for i in range(17)], value=-0.5, label="α", show_value=True)
    demo1_dt = mo.ui.slider(steps=[0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0], value=0.001, label="dt", show_value=True)
    mo.hstack([demo1_a, demo1_dt])
    return demo1_a, demo1_dt


@app.cell(hide_code=True)
def _(demo1_a, demo1_dt, plt, ref_integrate_exponential):
    _x, _t = ref_integrate_exponential(demo1_a.value, 1.0, demo1_dt.value, 10)
    _fig, _ax = plt.subplots()
    _ax.plot(_t, _x.real); _ax.set_xlabel("Time (s)"); _ax.set_ylabel("x")
    _fig
    return
```
Then the explanation as `mo.accordion({"Explanation": mo.md(...)})`, using the text from source lines 516-532, followed by `feedback_link(...)`.

**Step 7:** `uv run pytest -v`. Expected: all PASS.

**Step 8:** `uv run marimo-book build --strict`. Then open `_site/` (via `marimo-book serve`) and confirm:
- the exercise shows the yellow "Complete Coding Exercise 1" callout
- the solution accordion opens to code and an xkcd plot
- moving the Demo 1 sliders swaps figures without a kernel

If the build log says precompute skipped Demo 1, record why and adjust the steps.

**Step 9:**
```bash
git add -A content tests
git commit -m "feat(W2D1): port Section 1 with exercise/solution pattern and precomputed demo"
```

---

### Task 7: W2D1 port, part 3: Section 2 (oscillatory dynamics)

**Step 1:** Port the heading, timing note, `video_tabs("vPYQPI4nKT8", "BV1gZ4y1u7PK")`, feedback and prose (source lines 541-611).

**Step 2:** Demo 2 (hidden). Coarsen to 9 × 12 = 108 combinations. Keep `dt=0.0001, T=5` from the source:
```python
demo2_real = mo.ui.slider(steps=[round(-2 + 0.5 * i, 1) for i in range(9)], value=0.0, label="real", show_value=True)
demo2_imag = mo.ui.slider(steps=list(range(-4, 8)), value=3, label="imaginary", show_value=True)
```
The plot cell calls `ref_integrate_exponential(complex(demo2_real.value, demo2_imag.value), 1.0, 0.0001, 5)`, with `ax.grid(True)`.

**Step 3:** Add a test that guards the runtime budget:
```python
def test_demo2_single_render_under_1s():
    import time
    defs = run_notebook(NB)
    t0 = time.perf_counter()
    defs["ref_integrate_exponential"](complex(0, 3), 1.0, 0.0001, 5)
    assert time.perf_counter() - t0 < 1.0
```
If it fails on CI hardware, vectorize the reference or drop to `dt=0.001`. Note in the prose that the step is coarser than the original.

**Step 4:** Explanation accordion (source lines 636-650), then feedback.

**Step 5:**
```bash
uv run pytest -v && uv run marimo-book build --strict
```
Check the build log for precompute status on this page. If precompute declines two widgets on one page, accept it: the read view shows the default figure, and the workbench Edit view gives full interactivity. Mention this in the prose: "Click **Edit** to explore freely."

**Step 6:** `git commit -am "feat(W2D1): port Section 2 oscillatory dynamics"`

---

### Task 8: W2D1 port, part 4: Section 3 (2D dynamics)

**Step 1: Failing test first**
```python
def test_ref_system_linear():
    defs = run_notebook(NB)
    out = defs["ref_system"](0.0, np.array([1.0, 2.0]), 2, -5, 1, -2)
    np.testing.assert_allclose(out, [2*1 - 5*2, 1*1 - 2*2])

def test_system_stub_raises():
    import pytest
    defs = run_notebook(NB)
    with pytest.raises(NotImplementedError):
        defs["system"](0.0, np.array([1.0, 2.0]), 2, -5, 1, -2)
```
Run it and expect a FAIL.

**Step 2:** Port the Section 3 heading, timing, video (IDs at source lines ~700-712), the prose including the recap `<details>`, and the Coding Exercise 3 prose.

**Step 3:** Use the same pattern as Task 6:
- **Stub cell:** `system`, raising `NotImplementedError`.
- **Guarded try-it cell:** `plot_trajectory(system, ...)` inside try/except, with `_T, _dt, _A, _x0` locals.
- **Hidden solution cell:** `_src` string, `exec`, then `ref_system`. Render with `plt.xkcd()` inside the accordion.

**Step 4:** Demos 3A and 3B. Use dropdowns with labeled options, which precompute supports. The `None` option from the source is dropped:
```python
demo3a_A = mo.ui.dropdown(options={
    "[[2,-5],[1,-2]]": [[2, -5], [1, -2]],
    "[[3,4],[1,2]]": [[3, 4], [1, 2]],
    "[[-1,-1],[0,-0.25]]": [[-1, -1], [0, -0.25]],
    "[[3,-2],[2,-2]]": [[3, -2], [2, -2]],
}, value="[[2,-5],[1,-2]]", label="A")
```
3B uses the same pattern for `x0` with 3 options. Both plot cells call `plot_trajectory(ref_system, ...)`. Follow each with its explanation accordion and feedback link.

**Step 5:** `uv run pytest -v && uv run marimo-book build --strict`. Expected: PASS.

**Step 6:** `git commit -am "feat(W2D1): port Section 3 2D dynamics"`

---

### Task 9: W2D1 port, part 5: Section 4, summary and workbench check

**Step 1:** Port Section 4:
- prose
- "Think! 4"
- a hidden stream-plot cell: `A_options` as a local `_A_options`, and `plot_specific_example_stream_plots(_A_options)` as the last expression
- the explanation accordion
- feedback
- Summary (source lines 1001-end)

**Step 2:** `uv run marimo-book sync-deps`. Expected: a PEP 723 `# /// script` block appears at the top of the notebook (numpy, scipy, matplotlib).

**Step 3:** Pyodide reachability check for the workbench:
```bash
uv run marimo-book build --strict
uv run marimo-book serve
```
Open the W2D1 page in a browser, click **Edit**, wait for the kernel, and append `?wblog=1` if there are problems. Check:
- (a) all cells run
- (b) editing `integrate_exponential` with the solution makes the "try it" plot appear
- (c) after a reload, the edit is still there
- (d) "Reset to published" restores the stub

Write the results into the commit body.

**Step 4:** Compare against the original with a side-by-side read of the source `.md` and the rendered page. Check that every prose paragraph, equation, video, exercise, explanation and demo is present. Fix any gaps.

**Step 5:**
```bash
git add -A content
git commit -m "feat(W2D1): complete LDS port; verified workbench edit in Pyodide"
```

---

### Task 10: Cached-mode heavy demo (W2D1 Tutorial 2)

Proves the "static output for compute-intensive pages" path end to end.

**Files:**
- Create: `content/W2D1_Examples/W2D1_Tutorial2_Heavy.py`
- Create: `_rendered/` (generated, committed)
- Modify: `book.yml`

**Step 1:** Write a short notebook, "Fitting a linear dynamical system with gradient descent (PyTorch)":
1. Simulate 2D LDS trajectories with A = [[-0.1,-1],[1,-0.1]] using numpy.
2. Fit a `torch.nn.Linear(2,2,bias=False)` one-step predictor for 3000 epochs on CPU, logging the loss.
3. Plot the loss curve and true vs learned eigenvalues.

Keep the total runtime around 1–3 minutes. Add an explicit "Why is this page static?" callout explaining cached mode.

**Step 2:** TOC entry:
```yaml
      - file: content/W2D1_Examples/W2D1_Tutorial2_Heavy.py
        mode: cached
        views: [read]
```

**Step 3:**
```bash
uv sync --group heavy
uv run marimo-book render
```
Expected: `_rendered/` contains the page body and `_rendered/img/*.webp`.

**Step 4:** `uv run marimo-book render --check`. Expected: exit 0.

**Step 5: Prove CI needs no torch**
```bash
uv sync --no-group heavy
uv run marimo-book build --strict
```
Expected: exit 0, and the page shows the plots.

**Step 6: Prove staleness detection**
Append a comment line to the notebook, then run `uv run marimo-book render --check`. Expected: non-zero exit. Revert the comment and confirm exit 0 again.

**Step 7:** `uv run pytest -v`. The heavy notebook is skipped because torch is absent.

**Step 8:**
```bash
git add content/W2D1_Examples/W2D1_Tutorial2_Heavy.py _rendered book.yml
git commit -m "feat(W2D1): add cached-mode heavy PyTorch demo"
```

---

### Tasks 11–13: Rewrite W1D1–W1D3 as marimo-book meta-tutorials

These follow the same procedure for each day. Each tutorial is a short marimo notebook (about 80–150 lines) that *demonstrates* what it teaches. Each day also gets a `chapter_intro.md` and a `further_reading.md`, ported from the MyST originals with their content updated:
- The schedule table stays.
- Learning objectives are rewritten.
- Links point to marimo.io and marimobook.org docs.

**Per-tutorial procedure:**
1. Write the notebook.
2. Add it to the `book.yml` TOC.
3. `uv run pytest -v`
4. `uv run marimo-book build --strict`
5. Check it in `marimo-book serve`.
6. Commit one commit per day: `feat(W1Dx): rewrite as marimo tutorials`.

**Task 11 — `content/W1D1_GettingStarted/`**

| File | Must demonstrate |
|---|---|
| `W1D1_Tutorial1.py` "Anatomy of a marimo notebook" | Cells as functions, reactivity (changing a variable reruns dependents), `mo.md` with interpolated values, the single-definition rule, `_` local names |
| `W1D1_Tutorial2.py` "Book structure" | Annotated `book.yml` snippet (shown as a code block), TOC sections, `.md` vs `.py` pages, per-page `mode`/`views` overrides |
| `W1D1_Tutorial3.py` "Figures, math, callouts" | A matplotlib figure, inline and display math including `align`, `mo.callout` kinds, `mo.image` |
| `W1D1_Bonus.py` "Layout" | `mo.ui.tabs`, `mo.accordion`, `mo.hstack`/`vstack` |

**Task 12 — `content/W1D2_InteractiveContent/`**

| File | Must demonstrate |
|---|---|
| `W1D2_Tutorial1.py` "Widgets and static reactivity" | A `mo.ui.slider(steps=...)` and a dropdown driving a plot (precomputed). A continuous slider, with a note that it needs Edit. The precompute limits. |
| `W1D2_Tutorial2.py` "Exercises in the workbench" | A toy exercise (`def mean(xs): raise NotImplementedError`) using the full Task 6 pattern: stub, guarded try-it, hidden `_src` solution with `ref_`. Plus how students use Edit, Reset and history. |
| `W1D2_Tutorial3.py` "Choosing a render mode" | Comparison table of static / workbench / cached, and when to use each (as `mo.md`) |
| `W1D2_Bonus.py` "anywidget" | A minimal inline anywidget (counter) rendering statically. Add `anywidget` to `pyproject.toml` dependencies. |

**Task 13 — `content/W1D3_PublishingAndCI/`**

| File | Must demonstrate |
|---|---|
| `W1D3_Tutorial1.py` "The deploy workflow" | Walkthrough of `.github/workflows/deploy.yml`, step by step, plus the CNAME setup |
| `W1D3_Tutorial2.py` "Dependencies" | `pyproject.toml` groups, `sync-deps` and PEP 723, Pyodide package availability, the guarded micropip pattern for non-PyPI wheels (show the `_wheels` + `raw.githubusercontent.com` CORS note) |
| `W1D3_Tutorial3.py` "Heavy content with cached mode" | The `render` → commit `_rendered/` → `render --check` loop, linking to the W2D1 Tutorial 2 example |
| `W1D3_Bonus.py` "Scaling to a multi-week course" | Naming conventions `W{w}D{d}_*`, adding a day, TOC sections |

Pages without code can be `.md` instead of `.py`. Use `.py` only when the page runs something.

---

### Task 14: CI workflow

**Files:**
- Create: `.github/workflows/deploy.yml`
- Delete: `.github/workflows/generate-notebooks.yml`, `.github/workflows/publish-book.yml`, `.github/workflows/build-pyodide-wheels.yml`

**Step 1:** Write `deploy.yml`, reconciled with the Task 1 scaffold's workflow:
```yaml
name: Build and deploy book
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
      - run: uv sync --frozen
      - uses: actions/cache@v4
        with:
          path: .marimo_book_cache
          key: mbook-${{ hashFiles('uv.lock', 'book.yml') }}-${{ github.sha }}
          restore-keys: mbook-${{ hashFiles('uv.lock', 'book.yml') }}-
      - run: uv run pytest -v
      - run: uv run marimo-book check
      - run: uv run marimo-book sync-deps --check
      - run: uv run marimo-book render --check
      - run: uv run marimo-book build --strict
      - uses: actions/upload-pages-artifact@v3
        if: github.ref == 'refs/heads/main'
        with:
          path: _site
  deploy:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

**Step 2:** Validate the YAML:
```bash
uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))"
```

**Step 3:** Run the same commands locally, in order, to confirm each exits 0.

**Step 4:** `git rm` the old workflows, then commit with `ci: replace MyST workflows with marimo-book deploy`.

**Step 5:** Push the branch and open a draft PR so the workflow runs on `pull_request`. Expected: the build job is green and deploy is skipped.

---

### Task 15: Remove MyST artifacts

**Step 1:**
```bash
git rm -r myst.yml requirements.txt scripts/ tutorials/ projects/ _static/ .nvmrc
```
Keep `_wheels/`, `CNAME`, `LICENSE` and `docs/`. Delete `_static/custom.css` only if it is still empty. If it has rules, port them to marimo-book's theme config (see the Task 1 scaffold) or drop them.

**Step 2:**
```bash
uv run pytest -v && uv run marimo-book build --strict
```
Expected: PASS, so nothing referenced the removed files.

**Step 3:** Search for leftovers: `rg -n "myst|jupytext|kernelspec|notebooks-branch|colab" --glob '!docs/plans/**'`. Expected: no hits outside intentional prose (for example, a "Colab is not supported" note).

**Step 4:** `git commit -m "chore: remove MyST/JupyterLite toolchain"`

---

### Task 16: Rewrite AGENTS.md and README.md

**Step 1:** Rewrite `AGENTS.md` around the new architecture. Keep its structure: Project Overview, Architecture tree, Key files, Key Conventions, Build & CI, Pyodide, and "Converting .ipynb to marimo" (replacing the MyST conversion section). It must cover:
- the marimo single-definition rule and `_` locals
- last-expression output
- `hide_code=True`
- the full exercise/solution pattern from Task 6 (stub / guarded try-it / `_src`+`exec` → `ref_*`)
- precompute limits and the discrete-steps rule
- the `mode: cached` workflow
- `sync-deps`
- the ipywidgets → `mo.ui` mapping
- the vibecheck limitation
- MathJax (KaTeX notes removed)
- the local commands
- the CI steps
- for `.ipynb` → marimo conversion, `uv run marimo convert notebook.ipynb -o content/...py` as the first step, followed by the checklist

**Step 2:** Rewrite `README.md` with a quickstart (`uv sync`, `marimo-book serve`), how to add a day, and how deploys work.

**Step 3:** `git commit -m "docs: rewrite AGENTS.md and README for marimo-book"`

---

### Task 17: Final verification and merge

Use @verification-before-completion. Every item needs evidence.

**Step 1: Clean build**
```bash
uv run marimo-book clean
uv run pytest -v
uv run marimo-book check
uv run marimo-book sync-deps --check
uv run marimo-book render --check
uv run marimo-book build --strict
```
All must exit 0.

**Step 2: Negative checks, once each, reverting afterwards**
- Remove a dependency from a PEP 723 block → `sync-deps --check` fails.
- Edit the heavy notebook → `render --check` fails.
- Make an exercise "try it" cell raise without the guard → `pytest` and `build --strict` fail.

**Step 3:** Watch the PR CI go green.

**Step 4:** Merge to `main` through the PR (@finishing-a-development-branch). Watch the deploy job.

**Step 5: Check the live site at https://template.neuromatch.io**
- The read view loads with no Pyodide network request (DevTools Network panel).
- W2D1 Edit boots the workbench and an exercise can be edited and run.
- Demo 1 sliders respond in read view.
- The cached page shows its plots.
- Search works.
- `CNAME` is still applied.

**Step 6:** After the live site is confirmed, delete the `notebooks-branch` remote branch: `git push origin --delete notebooks-branch`. Confirm with the user first.
