# Editable Code Cells (Hybrid Panels on JupyterLite): Design

**Date:** 2026-10-15
**Status:** Draft for review
**Supersedes:** `2026-09-30-editable-cells-overlay-plan.md` and the untracked
`2026-10-15-editable-code-cells-plan.md` (both: post-build DOM overlay on
MyST's rendered page). `2026-09-29-editable-code-cells-findings.md` is still
accurate background.

## Why

Students working through ordinary (non-scrolly) tutorial pages can't complete
exercises on the site. MyST's JupyterLite power button starts a kernel and
runs cells, but the code stays static text
([mystmd#443](https://github.com/jupyter-book/mystmd/issues/443), open since
2023). An exercise cell can only run in its unfinished state. Worse, the site's
run-all fallback then silently runs the reference solution, so the cell
"works" without the student writing anything. Today the only way to do an
exercise is to leave the site for Colab or Kaggle.

Scrolly pages (`layout: scrolly`) already have editable panels
(`plugins/scrolly/runnable.mjs`), but on a bare Pyodide runtime with no
ipywidgets, magics or IPython display. Normal tutorials are mostly converted
NMA notebooks and depend on all three (`@widgets.interact`,
`%config InlineBackend…`, `display()`), so that runtime can't simply be reused.

## Goals

- On every browser page (a page with `kernelspec`, not scrolly, not marked
  Colab), every visible code cell is an editor. Students edit, run and see their
  own result on the page.
- Existing content runs unchanged: `@widgets.interact`, magics, rich output,
  top-level `await micropip.install(...)`.
- Notebook semantics: one kernel per page, shared state, running a cell first
  runs earlier cells that haven't run. Earlier *unfinished* exercises run their
  reference solution so later cells work. The exercise the student explicitly
  runs never does.
- Heavy-compute pages can opt out with one frontmatter line. They show
  read-only code plus a clear "do this one in Colab" banner.
- Panel look is restylable from `_static/custom.css` through CSS variables, in
  light and dark mode.

## Non-goals

- Saving edits across reloads. v1 keeps edits in memory, and the design leaves
  room for `localStorage` later (see "Future work").
- Pre-rendered outputs. Browser pages show code only until a student runs a
  cell, as they do today. `myst build --execute` was designed and then
  deferred. It comes back together with the scrolly pre-render (see
  "Appendix: deferred pre-rendered outputs").
- Changing scrolly pages. They keep their own runtime for now (see "Future
  work" for moving them onto this one).
- Changing generated notebooks. `scripts/convert_to_notebooks.py`'s notebook
  output is untouched.
- Running Colab pages in the browser, even partially.
- Binder/JupyterHub kernels.

## Anti-goals (failure even if it "works")

- An exercise that shows the solution's output when the student runs it.
- Students typing work into a page that can't run it (editable Colab pages).
- Two Python runtimes on one page (MyST's power button and our panels).
- Breaking on React re-renders or client-side page changes. The old overlay
  plan's main risk.
- Requiring authors to rewrite existing `widgets.interact` demos.

## Decisions

| Decision | Who |
|---|---|
| Fix this for non-scrolly pages: students must be able to edit and run cells | user |
| Two kinds of page: **browser** (default) and **Colab** (author opts in) | user (split), my call (default = browser) |
| Colab pages: read-only code + banner, no in-browser editing or running | my recommendation, user didn't object |
| Edits in memory only for v1, persistence designed but deferred | user |
| CodeMirror 6 editor, style editable via CSS variables | user |
| No pre-rendered outputs in v1. `--execute` deferred, to revisit together with scrolly's `--render` | user |
| **Hybrid**: panels emitted at build time by our MyST plugin, running on the JupyterLite kernel MyST already ships (thebe-core/thebe-lite) | user chose after the spike |
| JupyterLite power button hidden site-wide | my call |
| Fresh kernel per page (no state shared between tutorials) | my call |
| Frontmatter key `runtime: colab` | my call |
| Pin `mystmd==1.11.0` (panels use its bundled thebe 0.5.0 API) | my call |

## Spike evidence (2026-10-15, throwaway, `/tmp/spike`)

A spike plugin replaced every code cell with an anywidget panel (CodeMirror 6
editor + thebe output), built with mystmd 1.11.0 and driven headless with
Playwright.

| Check | Result |
|---|---|
| MyST loads `thebe-core.min.js` / `thebe-lite.min.js` on executable pages, `window.thebeCore.api` usable | ✓ |
| CodeMirror 6 inside MyST's anywidget shadow root | ✓ |
| `cell.execute(source)` runs the *edited* code (student edit → `10`) | ✓ |
| print, shared state between cells, matplotlib + `%config`, tracebacks | ✓ |
| `@widgets.interact` renders, moving the slider redraws the plot | ✓ |
| `display(HTML)`, pandas table | ✓ |
| Output placed in light DOM and slotted into the shadow root gets thebe/widget CSS | ✓ |
| Client-side navigation and back button, fresh kernel per page | ✓ |
| W2D1 Tutorial 1 (11 cells) top to bottom | ✓ except exercises (no fallback in spike) |
| First run (boot + `micropip` ipywidgets) | 6–8 s |
| First numpy/matplotlib import | ~5 s, then 10–400 ms per cell |
| CM6 + lang-python bundle | 467 KB min, 156 KB gzip |
| `myst build --execute`: outputs available to a `document`-stage plugin transform | ✓ (see below) |

Findings that shape the design (the `--execute` ones matter for the deferred
appendix):

- **Execution runs before plugin transforms.** At `stage: 'document'` each code
  block is `block{kind: 'notebook-code'} > [code, outputs > output*]`, and each
  `output.jupyter_data` is a plain nbformat output (`stream`, `display_data`
  with base64 `image/png`, `error`, widget views as `text/plain` +
  `application/vnd.jupyter.widget-view+json`).
- **`myst build --execute` exits 0 when a cell raises.** It logs
  `⛔️ <file> An exception occurred during code execution, halting further
  execution` and stops that page. `--strict` would also fail on unrelated
  warnings (e.g. W1D1 Tutorial 3's `.txt` image), so CI checks the log itself.
- **Panels may mount twice during hydration** (22 hosts briefly for 11 cells).
  Render must be idempotent, and state must live in the page runtime, not the
  widget instance.
- **CodeMirror's default keymap takes Shift-Enter.** Run bindings need
  `Prec.highest`.
- **thebe loads from outside services:** Pyodide 0.27 and widget JS from
  `cdn.jsdelivr.net`, `require.js` + MathJax 2.7 + font-awesome from
  `cdnjs.cloudflare.com`. JupyterLite probes `/pypi/all.json` and
  `/api/contents/all.json` (404, harmless).
- Power button selector: `.myst-jp-nb-toolbar-power`. Theme toggle sets
  `html.light` / `html.dark`.

## Architecture

```
 build time (CI)                                    browser
 ───────────────                                    ───────
 tutorials/*.md
   │ convert_to_notebooks.py --prepare-site
   │   badges, fallback cell (browser pages only)
   ▼
 myst build --html
   ▼
 plugins/cells/cells.mjs (document stage)
   │ browser page:  code blocks → runtime widget + panel widgets
   │ colab page:    leave code static, add banner
   ▼
 _build/html  ───────────────────────────────────▶  runtime widget (hidden)
                                                     window.NMA_CELLS = {path, cells}
                                                    panel widget (per visible cell)
                                                     shadow root: CodeMirror 6 + toolbar
                                                     light DOM:   output (slotted)
                                                         │ Run
                                                         ▼
                                                    plugins/cells/src/runtime.mjs
                                                     thebe-core → JupyterLite kernel
                                                     (Pyodide 0.27 in a worker, IPython,
                                                      ipywidgets via thebe widget manager)
```

### Files

```
plugins/cells/
  cells.mjs              # MyST plugin: page classification, panels, Colab banner
  cells.css              # panel styles (in each panel's shadow root)
  page.css               # page-level rules, copied into <head> by the runtime widget
  src/
    model.mjs            # pure helpers, no dependencies (unit-tested with node --test)
    editor.mjs           # CodeMirror 6 setup (keymap, theme from CSS variables)
    runtime.mjs          # kernel lifecycle, run queue, fallback control
    panel.mjs            # anywidget render(): editor + toolbar + output
    runtime-widget.mjs   # anywidget render() for the hidden page runtime node
  dist/
    panel.mjs            # GENERATED single-file bundle (esbuild), committed
    runtime-widget.mjs   # GENERATED, committed
  package.json           # pinned codemirror/@codemirror/* + esbuild, "build" script
  package-lock.json
scripts/
  convert_to_notebooks.py   # --prepare-site: no fallback cell on colab pages
  nma_solutions.py          # fallback transformer: honour "# nma-no-fallback"
  nma_cells.py              # is_colab / runtime_of + validation (Python side)
tests/
  js/cells.test.mjs
  test_nma_cells.py
  fixtures/cells/runtime.json   # shared Python/JS fixture for runtime_of
  e2e/test_cells_browser.py     # Playwright smoke test (from the spike harness)
_static/custom.css              # hides the power button site-wide
```

`runtime_of(text)` / `runtimeOf(text)` are two copies of the same rule. They
are tested against `tests/fixtures/cells/runtime.json`, following the existing
`is_scrolly`/`isScrolly` pattern.

## Authoring model

Nothing changes for browser pages. A heavy page adds one line:

```yaml
---
title: "Tutorial 3: Training a CNN"
runtime: colab            # read by plugins/ and scripts/; MyST warns "extra key ignored: runtime"
kernelspec:
  name: python3
  display_name: Python 3
---
```

Rules (enforced by `convert_to_notebooks.py`'s content validation, both modes):

- `runtime` is `browser` (the default, may be omitted) or `colab`. Anything else
  is an error.
- `runtime: colab` requires `kernelspec`, and can't be combined with
  `layout: scrolly`.

```python
# scripts/nma_cells.py
RUNTIMES = ("browser", "colab")
RUNTIME_RE = re.compile(r"^runtime:\s*['\"]?([A-Za-z]+)['\"]?\s*$", re.M)

def runtime_of(text: str) -> str:
    """'browser' or 'colab' (or the raw invalid value, for validate())."""
    m = RUNTIME_RE.search(nma_scrolly._frontmatter_text(text))  # make it public: frontmatter_text
    return m.group(1) if m else "browser"

def validate(text: str) -> list[str]:
    errors = []
    runtime = runtime_of(text)
    if runtime not in RUNTIMES:
        errors.append(f"runtime: {runtime!r} must be one of {', '.join(RUNTIMES)}")
    if runtime == "colab" and nma_scrolly.is_scrolly(text):
        errors.append("runtime: colab can't be combined with layout: scrolly")
    return errors
```

## Build time

### 1. `--prepare-site` (CI-only, on the throwaway checkout)

One change to `prepare_site_md` in `scripts/convert_to_notebooks.py`: **no
fallback cell on Colab pages**, since they never run on the site.

```python
# in prepare_site_md(), replacing the current `pairs = ...` line:
skip = nma_scrolly.is_scrolly(content) or nma_cells.runtime_of(content) == "colab"
pairs = [] if skip else nma_solutions.exercise_pairs(body)
```

The fallback cell stays exactly as it is today on browser pages. In the panels'
kernel it makes earlier unfinished exercises run their solution.

### 2. Fallback opt-out marker (`scripts/nma_solutions.py`)

The transformer must not replace the cell the student explicitly ran. The panel
appends a marker comment line to that cell's source. A trailing line doesn't
shift traceback line numbers.

```python
NO_FALLBACK_MARKER = "nma-no-fallback"   # keep in sync with plugins/cells/src/model.mjs

# in FALLBACK_TEMPLATE's nma_exercise_fallback():
    def nma_exercise_fallback(lines):
        source = "".join(lines)
        if (not unfinished.search(source)
                or "nma-exercise-fallback" in source
                or "$no_fallback" in source):
            return lines
        ...
```

Notebooks are unaffected because they don't get the fallback cell at all.

### 3. The plugin: `plugins/cells/cells.mjs`

Registered in `myst.yml` after the scrolly plugin. Document stage. It touches
only browser and Colab pages, and leaves scrolly pages and pages without
`kernelspec` alone.

```js
import { readFileSync } from 'node:fs';
import { isScrolly } from '../scrolly/scrolly.mjs';
import { runtimeOf, modeOf, isExercise } from './src/model.mjs';

const PANEL_ESM = '/plugins/cells/dist/panel.mjs';
const RUNTIME_ESM = '/plugins/cells/dist/runtime-widget.mjs';
const PANEL_CSS = '/plugins/cells/cells.css';
const PAGE_CSS = '/plugins/cells/page.css';

const isCodeBlock = (n) => n.type === 'block' && n.kind === 'notebook-code';
const codeOf = (b) => (b.children ?? []).find((c) => c.type === 'code')?.value ?? '';
const tagsOf = (b) => [b.data?.tags ?? []].flat();
const frontmatterOf = (src) => src.match(/^---\n([\s\S]*?)\n---/)?.[1] ?? '';

/** Rebuild a browser page in place. Exported for tests. */
export function buildBrowserPage(tree) {
  const cells = [];
  const walk = (node) => {
    node.children = (node.children ?? []).flatMap((child) => {
      if (!isCodeBlock(child)) {
        walk(child);
        return [child];
      }
      const code = codeOf(child);
      const cell = {
        index: cells.length,
        code,
        mode: modeOf(tagsOf(child)),        // edit | collapsed | output | hidden
        exercise: isExercise(code),
      };
      cells.push(cell);
      if (cell.mode === 'hidden') return [];  // runs from the manifest, no panel
      return [{
        type: 'block',
        children: [{
          type: 'anywidget',
          esm: PANEL_ESM,
          css: PANEL_CSS,
          class: 'nma-cell',
          id: `nma-cell-${cell.index}`,
          model: cell,
        }],
      }];
    });
  };
  walk(tree);
  const runtime = {
    type: 'anywidget',
    esm: RUNTIME_ESM,
    css: PAGE_CSS,
    class: 'nma-cells-runtime',
    id: 'nma-cells-runtime',
    model: { cells: cells.map(({ index, code, mode, exercise }) => ({ index, code, mode, exercise })) },
  };
  tree.children = [{ type: 'block', children: [runtime] }, ...tree.children];
  return cells.length;
}

/** Colab page: keep MyST's static code, add a banner at the top. */
export function buildColabPage(tree, { colabUrl, kaggleUrl }) {
  const banner = {
    type: 'admonition',
    kind: 'important',
    class: 'nma-colab-banner',
    children: [
      { type: 'admonitionTitle', children: [{ type: 'text', value: 'Do this tutorial in Colab' }] },
      { type: 'paragraph', children: [
        { type: 'text', value: 'This tutorial needs more computing power than your browser has, so its code can’t run on this page. ' },
        { type: 'link', url: colabUrl, children: [{ type: 'text', value: 'Open in Colab' }] },
        { type: 'text', value: ' or ' },
        { type: 'link', url: kaggleUrl, children: [{ type: 'text', value: 'Kaggle' }] },
        { type: 'text', value: ' to edit and run it.' },
      ] },
    ],
  };
  tree.children = [{ type: 'block', children: [banner] }, ...tree.children];
}

const cellsTransform = {
  name: 'nma-cells',
  doc: 'Editable, runnable code cells on browser pages; a Colab banner on runtime: colab pages.',
  stage: 'document',
  plugin: () => (tree, vfile) => {
    let source = '';
    try { source = readFileSync(vfile.path, 'utf8'); } catch { return; }
    if (!/^kernelspec:/m.test(frontmatterOf(source)) || isScrolly(source)) return;
    if (runtimeOf(source) === 'colab') buildColabPage(tree, notebookUrls(vfile.path));
    else buildBrowserPage(tree);
  },
};

export default { name: 'Neuromatch editable cells', transforms: [cellsTransform] };
```

`notebookUrls(path)` builds the same Colab/Kaggle URLs as
`make_badge_html()` in `convert_to_notebooks.py`, reusing `githubRepo()` /
`pageLocation()` from `plugins/nma.mjs` (export them). A shared fixture keeps
the URL formats in sync.

## Browser

### Page runtime widget (`runtime-widget.mjs`)

A hidden anywidget at the top of each browser page. It publishes the manifest,
copies `page.css` into `<head>` (same trick as `plugins/scrolly/engine.mjs`),
and renders nothing.

```js
import { pageRuntime } from './runtime.mjs';

export default {
  render({ model, el }) {
    const css = el.getRootNode().querySelector('link[rel=stylesheet], style');
    if (css && !document.getElementById('nma-cells-page-css')) {
      const copy = css.cloneNode(true);
      copy.id = 'nma-cells-page-css';
      document.head.appendChild(copy);
    }
    pageRuntime().setCells(model.get('cells'));   // resolves panels waiting on the manifest
  },
};
```

### Runtime (`runtime.mjs`)

One runtime per page path, shared on `window`. Everything that has to survive
a panel remount lives here: edits, which cells ran, the thebe cells and their
output areas.

```js
const STARTING = 'Starting Python… the first run takes about 10 seconds';

class PageRuntime {
  constructor(path) {
    this.path = path;
    this.cells = null;            // manifest from the runtime widget
    this.edits = {};              // index -> edited source (in memory only, v1)
    this.ran = new Set();         // indices run in the current kernel
    this.kernel = null;           // Promise<{api, config, server, rendermime, session, nb}>
    this.queue = Promise.resolve();
    this.listeners = new Set();   // panels, for status updates
    this.outs = new Map();        // index -> the panel's current light-DOM output element
    this.cellsReady = new Promise((r) => (this._resolveCells = r));
  }

  setCells(cells) { this.cells = cells; this._resolveCells(cells); }

  subscribe(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  emit(event) { for (const fn of this.listeners) fn(event); }

  /**
   * A panel hands over its output element (again after a remount). Every
   * registered cell is attached, not just the one clicked, so outputs of
   * earlier cells run automatically (and the fallback note) show in their
   * own panels.
   */
  register(index, el) {
    this.outs.set(index, el);
    if (this.ready) this.ready.nb.getCellById(thebeId(this.path, index)).attachToDOM(el);
    return () => { if (this.outs.get(index) === el) this.outs.delete(index); };
  }

  /** Boot thebe-lite once per page. */
  boot() {
    this.kernel ||= (async () => {
      this.emit({ kernel: 'starting', message: STARTING });
      await ensureThebeLoaded();                // /thebe-core.min.js, /thebe-lite.min.js
      const api = window.thebeCore.api;
      const events = api.makeEvents();
      const config = api.makeConfiguration({ useJupyterLite: true }, events);
      const server = api.makeServer(config);
      await server.connectToJupyterLiteServer();
      const rendermime = api.makeRenderMimeRegistry(config.mathjax);
      const cells = await this.cellsReady;
      const nb = api.setupNotebookFromBlocks(
        cells.map((c) => ({ id: thebeId(this.path, c.index), source: c.code })),
        config, rendermime,
      );
      const session = await server.startNewSession(rendermime);
      nb.attachSession(session);
      this.ready = { api, config, server, rendermime, session, nb };
      // attachToDOM replaces the element's contents (e.g. the "Run to see output" hint).
      for (const [index, el] of this.outs) nb.getCellById(thebeId(this.path, index)).attachToDOM(el);
      this.emit({ kernel: 'ready' });
      return this.ready;
    })();
    return this.kernel;
  }

  /**
   * Run cell `index` the way a notebook would: earlier unrun cells first (an
   * unfinished earlier exercise runs its solution via the kernel-side
   * fallback), then the target with the fallback switched off.
   */
  run(index, source) {
    const job = this.queue.then(async () => {
      const k = await this.boot();
      for (const c of this.cells) {
        if (c.index >= index) break;
        if (this.ran.has(c.index)) continue;
        await this.exec(k, c.index, this.edits[c.index] ?? c.code);   // fallback allowed
      }
      return this.exec(k, index, withNoFallback(source));
    });
    this.queue = job.catch(() => {});
    return job;
  }

  async exec(k, index, source) {
    const cell = k.nb.getCellById(thebeId(this.path, index));
    this.emit({ index, state: 'running' });
    const res = await cell.execute(source);         // null on internal failure
    this.ran.add(index);
    const error = res === null ? { ename: 'InternalError' } : res.error?.[0] ?? null;
    this.emit({ index, state: error ? 'error' : 'done', count: cell.executionCount, error });
    return { error };
  }

  async restart() {
    const k = await this.kernel;
    await k.session.kernel.restart();   // verify API name in Task 0a
    this.ran.clear();
    this.emit({ kernel: 'ready', restarted: true });
  }

  async dispose() {
    if (!this.kernel) return;
    const k = await this.kernel.catch(() => null);
    await k?.server.shutdownAllSessions();
    k?.server.dispose();
  }
}

/** One runtime per page; switching pages shuts the old kernel down. */
export function pageRuntime() {
  const path = location.pathname;
  const W = (window.NMA_CELLS ||= {});
  if (W.runtime?.path !== path) {
    W.runtime?.dispose();
    W.runtime = new PageRuntime(path);
  }
  return W.runtime;
}
```

```js
// plugins/cells/src/model.mjs (pure, unit-tested)
export const NO_FALLBACK_MARKER = 'nma-no-fallback';     // sync: scripts/nma_solutions.py
export const UNFINISHED_RE = /^[ \t]*raise NotImplementedError/m;  // sync: nma_solutions.py

export const isExercise = (code) => UNFINISHED_RE.test(code);

/** Append the marker as a trailing comment line (doesn't shift tracebacks). */
export const withNoFallback = (src) =>
  src.includes(NO_FALLBACK_MARKER) ? src : `${src.replace(/\s*$/, '')}\n# ${NO_FALLBACK_MARKER}\n`;

export function modeOf(tags) {
  if (tags.includes('remove-cell')) return 'hidden';
  if (tags.includes('remove-input')) return 'output';
  if (tags.includes('hide-input') || tags.includes('hide-cell')) return 'collapsed';
  return 'edit';
}
```

Behaviour notes:

- **Hidden cells** (`remove-cell`, including the injected fallback cell) are in
  the manifest and run as "earlier cells". They have no panel, and their output
  attaches nowhere.
- **The fallback note** ("Exercise not completed yet, so the reference solution
  was run.") prints into the *earlier* exercise's own panel, because the output
  goes to whichever cell ran.
- **Page changes:** `pageRuntime()` keys on `location.pathname`. The first
  panel or runtime widget rendered on a new page disposes the old runtime, which
  shuts down its Pyodide worker. Coming back means a fresh kernel. (My call: no
  state leaks between tutorials, at the cost of a reboot.)
- **Loading thebe:** MyST already loads `thebe-core.min.js` and
  `thebe-lite.min.js` on executable pages, so `ensureThebeLoaded()` first waits
  for `window.thebeCore.api` and `window.thebeLite`. If they're missing, it
  injects them relative to the bundle, `new URL('../thebe-core.min.js',
  import.meta.url)`. The bundle is served from `<site base>/build/`, so this
  also works for forks deployed under `github.io/<repo>/`. Never use a
  root-absolute `/thebe-core.min.js`.
- **Restart:** each panel's bar gets a "Restart" button once the kernel is up.
  It restarts the kernel, clears `ran`, and resets the run queue, so a hung
  cell doesn't block later runs.
- **Errors:** `res.error` comes from thebe (spike: `✗ NotImplementedError`).
  Running stops at the first earlier cell that errors, and its panel shows the
  traceback.

### Panel (`panel.mjs`)

```js
import { createEditor } from './editor.mjs';
import { pageRuntime } from './runtime.mjs';

const LABEL = { edit: 'Python', collapsed: 'Python · code hidden', output: 'Output' };

export default {
  render({ model, el }) {
    const index = model.get('index');
    const mode = model.get('mode');
    const exercise = model.get('exercise');
    const original = model.get('code');
    const rt = pageRuntime();
    const host = el.getRootNode().host;

    el.innerHTML = `
      <div class="cell${exercise ? ' is-exercise' : ''}" data-mode="${mode}">
        <div class="bar">
          <span class="label">${exercise ? 'Exercise · fill in, then run' : LABEL[mode]}</span>
          <button class="run" type="button" aria-label="Run cell">▶ Run</button>
          ${mode !== 'output' ? '<button class="reset" type="button">Reset</button>' : ''}
          ${mode === 'collapsed' ? '<button class="toggle" type="button" aria-expanded="false">Show code</button>' : ''}
          <span class="status" role="status" aria-live="polite"></span>
        </div>
        <div class="editor" ${mode === 'collapsed' ? 'hidden' : ''}></div>
        <slot name="out"></slot>
      </div>`;

    // Output lives in light DOM so page CSS (thebe, ipywidgets) applies.
    // Idempotent: hydration can mount a panel twice.
    host.querySelectorAll(':scope > .nma-cell-out').forEach((n) => n.remove());
    const out = document.createElement('div');
    out.slot = 'out';
    out.className = 'nma-cell-out';
    host.appendChild(out);
    if (!rt.ready && mode === 'output') out.innerHTML = '<p class="nma-hint">Run to see output</p>';
    const unregister = rt.register(index, out);          // re-attaches the live output on remount

    const editor = mode === 'output' ? null : createEditor({
      parent: el.querySelector('.editor'),
      root: el.getRootNode(),
      doc: rt.edits[index] ?? original,                  // keep edits across remounts
      onChange: (text) => {
        if (text === original) delete rt.edits[index]; else rt.edits[index] = text;
        if (rt.ran.has(index)) out.classList.add('is-stale');  // "edited, run to update"
      },
      onRun: () => run(),
    });

    const status = el.querySelector('.status');
    const run = async () => {
      out.classList.remove('is-stale');
      await rt.run(index, editor ? editor.text() : original);   // boots on first use
    };

    const off = rt.subscribe((e) => {
      if (e.kernel === 'starting') status.textContent = e.message;
      if (e.index !== index) return;
      status.textContent = e.state === 'running' ? 'Running…'
        : e.state === 'error' ? `[${e.count ?? ' '}] ✗ ${e.error.ename}`
        : `[${e.count}] ✓`;
    });

    el.querySelector('.run').addEventListener('click', run);
    el.querySelector('.reset')?.addEventListener('click', () => editor.setText(original));
    el.querySelector('.toggle')?.addEventListener('click', (ev) => {
      const ed = el.querySelector('.editor');
      ed.hidden = !ed.hidden;
      ev.target.textContent = ed.hidden ? 'Show code' : 'Hide code';
      ev.target.setAttribute('aria-expanded', String(!ed.hidden));
    });

    return () => { off(); unregister(); editor?.destroy(); out.remove(); };
  },
};
```

Modes, matching scrolly and today's tag conventions:

| Tag | Panel |
|---|---|
| none | editor + output |
| `hide-input` / `hide-cell` | editor collapsed behind "Show code", output visible |
| `remove-input` | output only, Run button, no editor |
| `remove-cell` | no panel, runs as an earlier cell |
| exercise (no tags, by rule) | editor, "Exercise · fill in, then run" |

Before the first Run, panels show only code (output-only panels show a "Run
to see output" hint). After it, thebe owns the output area.

### Editor (`editor.mjs`)

```js
import { EditorView, keymap, lineNumbers, highlightActiveLine, drawSelection } from '@codemirror/view';
import { EditorState, Prec } from '@codemirror/state';
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { indentUnit, bracketMatching, syntaxHighlighting, HighlightStyle } from '@codemirror/language';
import { closeBrackets } from '@codemirror/autocomplete';
import { python } from '@codemirror/lang-python';
import { tags as t } from '@lezer/highlight';

// Colors come from CSS variables (see "Styling"), so courses restyle without JS.
const highlight = HighlightStyle.define([
  { tag: t.keyword, color: 'var(--nma-tok-keyword)' },
  { tag: [t.string, t.special(t.string)], color: 'var(--nma-tok-string)' },
  { tag: [t.number, t.bool, t.null], color: 'var(--nma-tok-number)' },
  { tag: t.comment, color: 'var(--nma-tok-comment)', fontStyle: 'italic' },
  { tag: [t.function(t.variableName), t.function(t.propertyName)], color: 'var(--nma-tok-function)' },
  { tag: [t.definition(t.variableName), t.className], color: 'var(--nma-tok-definition)' },
]);

const theme = EditorView.theme({
  '&': { color: 'var(--nma-cell-fg)', backgroundColor: 'var(--nma-cell-bg)', fontSize: 'var(--nma-cell-font-size)' },
  '.cm-content': { fontFamily: 'var(--nma-cell-font)', caretColor: 'var(--nma-cell-accent)' },
  '.cm-gutters': { backgroundColor: 'var(--nma-cell-gutter-bg)', color: 'var(--nma-cell-gutter-fg)', border: 'none' },
  '.cm-activeLine': { backgroundColor: 'var(--nma-cell-active-line)' },
  '&.cm-focused': { outline: '2px solid var(--nma-cell-accent)' },
});

export function createEditor({ parent, root, doc, onChange, onRun }) {
  const runKeys = Prec.highest(keymap.of([
    { key: 'Shift-Enter', run: () => (onRun(), true) },
    { key: 'Mod-Enter', run: () => (onRun(), true) },
  ]));
  const view = new EditorView({
    parent,
    root,                                   // the shadow root (spike: required)
    state: EditorState.create({
      doc,
      extensions: [
        runKeys, lineNumbers(), highlightActiveLine(), drawSelection(), history(),
        bracketMatching(), closeBrackets(), indentUnit.of('    '),
        keymap.of([indentWithTab, ...defaultKeymap, ...historyKeymap]),
        python(), syntaxHighlighting(highlight), theme,
        EditorView.contentAttributes.of({ 'aria-label': 'Python code' }),
        EditorView.updateListener.of((u) => u.docChanged && onChange(u.state.doc.toString())),
      ],
    }),
  });
  return {
    text: () => view.state.doc.toString(),
    setText: (s) => view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: s } }),
    destroy: () => view.destroy(),
  };
}
```

No `basicSetup`: the explicit list above is smaller and leaves out search and
autocomplete popups, which are of little use here. Tab indents. For keyboard
users, CodeMirror's standard behaviour applies: Esc, then Tab, moves focus on.
This is noted in the panel's `aria-describedby` hint.

Bundling: `plugins/cells/package.json` pins `codemirror`, `@codemirror/*`,
`@lezer/highlight` and `esbuild`. MyST copies each anywidget `esm` file on its
own, so each entry point must be a single self-contained file:

```json
{
  "private": true,
  "type": "module",
  "scripts": {
    "build": "esbuild src/panel.mjs src/runtime-widget.mjs --bundle --format=esm --minify --outdir=dist --banner:js=\"// GENERATED by npm run build in plugins/cells. Do not edit.\""
  }
}
```

`runtime.mjs` is imported by both entry points, so each bundle gets its own
copy of the module. They still share one runtime because state lives on
`window.NMA_CELLS`, not in module scope. Keep it that way.

`dist/` is committed, so `myst start` works without Node tooling. CI rebuilds it
and fails if the committed copy is out of date:

```yaml
      - name: Check editable-cells bundle is up to date
        working-directory: plugins/cells
        run: npm ci && npm run build && git diff --exit-code dist/
```

### Styling

All panel colors are CSS variables with built-in light and dark defaults.
Custom properties inherit through the shadow boundary, so a course overrides
them in `_static/custom.css` on `:root` / `html.dark`.

```css
/* plugins/cells/cells.css (inside each panel's shadow root) */
:host {
  --_bg: var(--nma-cell-bg-light, #fbfbfe);
  --_fg: var(--nma-cell-fg-light, #1f1d3a);
  /* … one private var per public token … */
}
:host([data-theme='dark']) {
  --_bg: var(--nma-cell-bg-dark, #1b1a2e);
  --_fg: var(--nma-cell-fg-dark, #e8e7ff);
}
.cell {
  --nma-cell-bg: var(--_bg);
  --nma-cell-fg: var(--_fg);
  border: 1px solid var(--nma-cell-border, rgba(42, 41, 82, 0.18));
  border-left: 4px solid var(--nma-cell-accent, #5e5cd6);
  border-radius: var(--nma-cell-radius, 8px);
}
.cell.is-exercise { border-left-color: var(--nma-cell-exercise-accent, #e8a33d); }
```

The panel keeps `data-theme` on its host in sync with `html.dark`/`html.light`
using a `MutationObserver` on `document.documentElement`'s `class`. Firefox
doesn't support `:host-context()`, so the observer is needed.

Public tokens (defaults in `cells.css`, documented in AGENTS.md):

| Token | Purpose |
|---|---|
| `--nma-cell-{bg,fg}-{light,dark}` | editor background / text |
| `--nma-cell-border`, `--nma-cell-radius` | frame |
| `--nma-cell-accent`, `--nma-cell-exercise-accent` | left rule, focus ring, caret |
| `--nma-cell-gutter-{bg,fg}`, `--nma-cell-active-line` | gutter, current line |
| `--nma-cell-font`, `--nma-cell-font-size` | code font |
| `--nma-tok-{keyword,string,number,comment,function,definition}` (`-light`/`-dark`) | syntax colors |

Example override:

```css
/* _static/custom.css */
:root { --nma-cell-accent: #2a9d8f; --nma-tok-keyword-light: #b5179e; }
html.dark { --nma-tok-keyword-dark: #f72585; }
```

### Page-level CSS

```css
/* _static/custom.css: JupyterLite's power button is replaced site-wide by the panels. */
.myst-jp-nb-toolbar-power { display: none !important; }

/* plugins/cells/page.css (copied into <head> by the runtime widget) */
.nma-cells-runtime { display: none; }
.nma-cell-out.is-stale { opacity: 0.55; }
.nma-cell-out.is-stale::before { content: 'Edited · run to update'; font-size: 0.75rem; }
```

MyST's own "Launch in external computing interface" button
(`.myst-fm-launch-button`) is left as is.

## Outside services

thebe-lite (as shipped by mystmd 1.11) loads:

| Host | What |
|---|---|
| `cdn.jsdelivr.net` | Pyodide 0.27, ipywidgets JS, katex/mpl CSS |
| `cdnjs.cloudflare.com` | `require.js` (widget manager), MathJax 2.7 (math in outputs), font-awesome |
| `pypi.org` / `files.pythonhosted.org` | `micropip.install` of pure-Python wheels |

Students' browsers normally reach all of these. Restricted networks are the
risk. Mitigations, deferred unless needed: self-host `require.js`, and point
thebe's MathJax option at jsdelivr to drop a host.

MyST's thebe-lite pins **Pyodide 0.27**. Scrolly panels load their own newer
Pyodide (`nma.scrolly.pyodide_url`). The two never share a page, but package
availability can differ between page types.

## Testing

**Unit (Node, no install):** `tests/js/cells.test.mjs` covers
`src/model.mjs` (`modeOf`, `isExercise`, `withNoFallback`, `runtimeOf`) and `buildBrowserPage`/`buildColabPage` on small ASTs: hidden cells
are in the manifest with no panel, Colab pages keep their code blocks, and scrolly pages and pages without `kernelspec`
are untouched.

**Python (pytest):** `tests/test_nma_cells.py` covers `runtime_of` (shared
fixture) and `validate`. `test_convert_to_notebooks.py` covers no fallback
cell on Colab pages. `test_nma_solutions.py` checks
that the transformer leaves a source containing `nma-no-fallback` alone, run in
a real IPython shell like the existing fallback tests.

**Browser smoke test (Playwright):** `tests/e2e/test_cells_browser.py`, grown
from the spike harness, runs against the built site in CI after `myst build`.
It needs network access for jsdelivr/cdnjs.

1. W2D1 Tutorial 1: panels = visible code cells, each with one editor and one
   output (after the hydration double-mount has settled).
2. Run the last cell. Earlier cells run, and an earlier unfinished exercise
   shows the fallback note.
3. Type a solution into exercise 1 and run it. Its own output appears, and no
   fallback note in that panel.
4. Run an unfinished exercise explicitly. It shows `NotImplementedError`, not
   solution output.
5. Euler `@widgets.interact`: slider renders, a keypress changes the image.
6. Navigate to another page and back. Panels re-render and a fresh kernel runs.
7. Colab page fixture: banner present, no `.nma-cell`, power button hidden.

A spike-only gotcha: Playwright can't intercept requests that go through
JupyterLite's service worker. In CI there's no need to intercept, so leave
service workers on.

## Implementation order

**Task 0: verify the unknowns (short spikes, findings appended here).**
- 0a. thebe API details not exercised in the spike: kernel restart
  (`session.kernel.restart()`?), `server.shutdownAllSessions()` + `dispose()`
  on page change, and `attachToDOM(el)` moving an already attached area to a
  new element after a remount. The spike's source read shows `attachToDOM`
  returning early with "already attached" only when its second argument is
  true, and otherwise re-appending `area.node`, so this should work, but
  confirm it in the browser. Also confirm that booting attaches every registered
  panel, so earlier cells run automatically show their output in place.

**Task 1: Python side.** `nma_cells.py` (+ validation wired into
`validate_content`), `--prepare-site` changes, fallback marker, tests.

**Task 2: plugin.** `cells.mjs`, `src/model.mjs`, `myst.yml` registration,
unit tests. Panels can be stubbed first (the textarea from scrolly) to land the
build-time half.

**Task 3: runtime + panel + editor.** `runtime.mjs`, `panel.mjs`,
`editor.mjs`, `runtime-widget.mjs`, CSS, bundling, committed `dist/`.

**Task 4: CI.** Bundle freshness check, Playwright smoke test.

**Task 5: docs and content.** AGENTS.md (new "Editable cells" section, Colab
pages, CSS tokens, outside services). Update W1D2's
interactive-content tutorials, which describe the power button. Add a Colab
page example (e.g. a small `runtime: colab` page under W2D1).

## Future work

- **Saving edits** (deferred by the user). `localStorage` key
  `nma-cells:<repo>:<page path>:<cell_key>`, where `cell_key` is the existing
  scrolly hash of the *original* code. Save only edited cells, delete on Reset.
  If the author changes a cell, its hash changes and the saved edit no longer
  matches. Offer "You have an older version of this cell. Restore it?" rather
  than overwriting or silently dropping work. The repo goes in the key because
  several courses may share a domain. `rt.edits` is already the single place
  edits live, so this is a load/save around it.
- **"Download my notebook"**: write the page with the student's edits to
  `.ipynb`. It's useful on its own, and it bridges to Colab when a page turns
  out to need it.
- **Scrolly on the same runtime and editor, plus pre-rendered outputs.** Swap
  scrolly's textarea for `editor.mjs` first (cheap). Moving scrolly onto the
  thebe runtime removes the second Pyodide and lets scrolly pages use
  ipywidgets, but `# @param` controls need rework. When scrolly is revisited,
  bring back pre-rendered outputs for both page types with one mechanism
  (`--execute`, see the appendix) in place of `nma_scrolly.py --render`.
- **Fewer outside hosts**: self-host `require.js`, configure MathJax.
- **Upstream:** if mystmd#443 ships native editing, re-evaluate whether the
  panels are still needed.

## Left to the builder

- Exact copy for banners, labels and the stale-output note (keep it short and
  plain).
- Default light/dark palette values (start from the scrolly panel colors for
  dark).

## Appendix: deferred pre-rendered outputs (`--execute`)

Deferred by the user on 2026-10-15, to be revisited together with scrolly's
`nma_scrolly.py --render`. Kept here so that work starts from what was already
designed and verified.

**Why it's wanted:** pages open with plots and printed results before anyone
presses Run (skimming, review, phones, linking to figures, no 6–8 s start just
to see a plot). Every build also runs every browser page, so a broken cell
fails CI. Today nothing checks normal pages.

**Why it's deferred:** CI time, a `jupyter_server` dependency, a log check
(`myst` exits 0 when a cell raises), page JSON size, extra panel states, and
every existing page has to run cleanly first. In the spike's run without the
fallback cell, W1D2 Tutorials 2 and 5 also halted. They may be exercises or
intentional errors.

**Verified in the spike:** MyST executes before `document`-stage plugin
transforms, so blocks arrive as `block > [code, outputs > output.jupyter_data]`
(plain nbformat). Pages opt out with frontmatter `execute: {skip: true}`, and
cells with the `skip-execution` / `raises-exception` tags.

**Design sketch:**

1. `--prepare-site` adds `execute: {skip: true}` to scrolly pages (if they keep
   `--render`) and Colab pages. Authors must not write `execute:` themselves
   (add a validation error).

```python
EXECUTE_SKIP = "execute:\n  skip: true\n"

def _with_execute_skip(frontmatter: str) -> str:
    """Insert `execute: {skip: true}` before the closing ---. Idempotent."""
    if "\nexecute:" in frontmatter:
        return frontmatter
    return frontmatter[:-3] + EXECUTE_SKIP + "---"
```

2. CI builds with `--execute` and fails on execution errors:

```yaml
      - name: Build MyST book
        run: |
          set -o pipefail
          uv run myst build --html --execute 2>&1 | tee myst-build.log
          if grep -q "An exception occurred during code execution" myst-build.log; then
            grep -A3 "An exception occurred during code execution" myst-build.log
            echo "::error::a page raised during execution (see above)"
            exit 1
          fi
```

   `requirements.txt` gains `jupyter_server`. Optionally cache `_build/execute`.
   CI runs CPython, so `sys.platform == "emscripten"` branches are skipped there,
   and a cell can pass in CI and still fail in Pyodide.

3. The fallback cell makes the run get past exercises (CI runs the solutions).
   So **exercise panels never show pre-rendered output**: it would be the
   solution's.

4. The plugin passes trimmed outputs to each panel:

```js
const outputsOf = (b) =>
  ((b.children ?? []).find((c) => c.type === 'outputs')?.children ?? [])
    .map((o) => o.jupyter_data).filter(Boolean);

// model: { ...cell, initial: cell.exercise ? [] : trimOutputs(outputsOf(child)) }

const WIDGET_MIME = 'application/vnd.jupyter.widget-view+json';
const KEEP = ['text/html', 'image/png', 'image/jpeg', 'image/svg+xml', 'text/plain'];

/** nbformat outputs -> what a panel shows before the kernel starts. */
export function trimOutputs(outputs) {
  const out = [];
  for (const o of outputs) {
    if (o.output_type === 'stream') out.push({ kind: 'stream', name: o.name, text: o.text });
    else if (o.output_type === 'error') out.push({ kind: 'error', text: stripAnsi(o.traceback.join('\n')) });
    else if (o.data?.[WIDGET_MIME]) out.push({ kind: 'widget' });   // "Run to use the controls"
    else if (o.data) {
      const mime = KEEP.find((m) => m in o.data);
      if (mime) out.push({ kind: 'data', mime, value: o.data[mime] });
    }
  }
  return out;
}
```

5. The panel renders `initial` with a small DOM renderer until the kernel boots
   (`stream` as `<pre>`, `image/*` as `<img>`, `text/html` as HTML, `error` as
   `<pre class="err">`, `widget` as a "Run to use the interactive controls"
   note). `register()` → `attachToDOM` then replaces it.
6. Measure page JSON size first. Base64 images in panel models land in the page
   JSON, whereas MyST normally extracts them to files. If it's too big, write
   images to `_build/site/public/` and pass URLs.
7. **Scrolly:** reading outputs from the AST could replace `--render`. Scrolly
   pages would then need the fallback cell too. That's safe on scrolly's bare
   Pyodide, because the fallback's `get_ipython()` returns `None` there and it
   does nothing.
