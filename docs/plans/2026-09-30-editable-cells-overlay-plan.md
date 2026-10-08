# Editable Code Cells (Overlay + thebe-core) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Students can edit any visible `{code-cell}` in the browser and re-run it on the JupyterLite (Pyodide) kernel. Widgets, `display()`, magics and rich output keep working.

**Supersedes:** `2026-09-29-thebe-core-subpath-fix-plan.md` (that work was done, then made unnecessary by the custom domain). This plan implements Option B from `2026-09-29-editable-code-cells-findings.md`.

**Architecture:**

- **Injection:** a post-build Python script adds `<link>` and `<script>` tags for a small overlay (`_static/editor/`) to every `_build/html/**/index.html`.
- **Editors:** the overlay finds each `div.myst-jp-nb-block`, hides the static `<pre>`, and mounts a vendored CodeMirror 5 editor with Run/Clear buttons in its place.
- **Kernel:** on the first Run, the overlay loads the thebe JS that MyST already emits (`/thebe-lite.min.js`, `/thebe-core.min.js`). It then uses the public `window.thebeCore.api` to connect to JupyterLite and build a notebook from the page's cells. Each Run calls `cell.execute(editor.getValue())`; `ThebeCell.execute(source)` accepts a source override.
- **Outputs:** they render through thebe's renderMime and widget manager, so ipywidgets keep working.
- **One kernel only:** MyST's own power-button toolbar is hidden with CSS.
- **No changes to tutorial `.md` files**, and no theme fork.

**Tech stack:** vanilla JS (no bundler), CodeMirror 5.65.x (vendored UMD), thebe-core/thebe-lite as emitted by mystmd 1.11.0, Python 3 (injection script, stdlib only), GitHub Actions.

**Decisions made with the user:**
- Post-build injection, not a fork or `{anywidget}`.
- Our own thebe session; MyST's power button is hidden.
- Every visible code cell is editable.
- Kernel loads lazily on the first Run.
- CodeMirror 5 is vendored.

---

### Task 0: Pin mystmd and spike the thebe-core API

The overlay depends on MyST's DOM class names and on thebe's bundled API. Pin the version so an upgrade can't silently break it.

**Files:** Modify `requirements.txt` (change `mystmd>=1.3` to `mystmd==1.11.0`).

**Step 1:** Rebuild: `uv run myst build --html`. The current `_build` is stale.

**Step 2: Spike in the browser.**
1. Serve the build: `python3 -m http.server -d _build/html 8000`.
2. Open `/tutorials/w1d1-gettingstarted/w1d1-tutorial1/` and confirm these in the DevTools console:
   - Plain `<script>` tags are enough to load thebe (no module bundler needed): add `<script src="/thebe-lite.min.js">` and `<script src="/thebe-core.min.js">` to the page, then check that `window.thebeCore.api` and `window.thebeLite` exist.
   - `const cfg = thebeCore.api.makeConfiguration({useJupyterLite: true}, events)`.
   - `const server = thebeCore.api.makeServer(cfg)`, then `await server.connectToJupyterLiteServer()`.
   - `const rendermime = thebeCore.api.makeRenderMimeRegistry(server.config.mathjax)`.
   - `const nb = thebeCore.api.setupNotebookFromBlocks([{id, source}], cfg, rendermime)`.
   - `const session = await server.startNewSession(rendermime)`, then `nb.attachSession(session)`.
   - `nb.getCellById(id).attachToDOM(el)`, then `await cell.execute("print(1)")`.
   - `@widgets.interact` renders working sliders.

**Step 3:** Write the exact working call sequence into `docs/plans/2026-09-30-thebe-api-notes.md`. Method names above may differ slightly; confirm them against `node_modules/thebe-core` type defs or the minified source.

**Exit criteria:** a confirmed call sequence that runs edited code and renders a widget. If widgets don't render this way, stop and revisit with the user before continuing.

### Task 1: Vendor CodeMirror 5

**Files:** create `_static/editor/vendor/codemirror.min.js`, `python.min.js`, `codemirror.min.css`, `LICENSE` (MIT).

- Download CodeMirror 5.65.18 from the npm tarball (`npm pack codemirror@5.65.18`). Copy in `lib/codemirror.js` (minify or use as-is), `mode/python/python.js`, `lib/codemirror.css`, and `LICENSE`.
- Add `_static/editor/vendor/README.md` recording the version and source URL.

### Task 2: Overlay JS, `_static/editor/nma-editor.js`

A single IIFE with no dependencies beyond the globals `CodeMirror` and `thebeCore`.

**Cell discovery (`scan()`):**
1. Select `article div.myst-jp-nb-block[id]` elements that contain `code.language-python`. Skip any already marked `data-nma-editor`.
2. Read the source from `code.textContent`. Server-side rendering includes it, and it survives client-side navigation.
3. Classify each cell:
   - **remove-cell:** the block has class `hidden`. It gets no editor and is queued as a setup cell.
   - **hide-input:** the code sits inside `details.myst-dropdown`. It gets an editor inside the existing `<details>`, so it stays collapsed until opened.
   - **regular:** an editor plus a toolbar.
4. Mount the editor: hide the `.myst-code` div by adding the `nma-hidden` class (don't remove it, because React owns it). Insert `<div class="nma-cell">` after it, containing a toolbar (Run, Clear, status) and a CodeMirror instance:
   - options: `mode: python`, `lineNumbers`, `indentUnit: 4`, `viewportMargin: Infinity`
   - `Shift-Enter` runs the cell
   - `Tab` inserts 4 spaces
5. Output target: the block's existing `[data-name=outputs-container]`. If attaching there conflicts with React re-renders during the spike, use our own `<div class="nma-output">` instead.

**Kernel lifecycle (`ensureKernel()`):** a memoised promise.
1. Inject the two thebe scripts and wait for the globals.
2. Connect to JupyterLite once per browser tab, so the server is reused across pages.
3. Start a session per page and build the notebook from all discovered cells.
4. Run the remove-cell setup cells silently, in order.
5. Report status in a page-level toolbar: "Starting kernel…", then "Ready", or an error message.

**Page toolbar:** inject a sticky bar at the top of `article` with Run all, Restart kernel, and a status pill. Restart means `session.restart()`, then clearing outputs and re-running the setup cells.

**Running:**
1. `await ensureKernel()`.
2. `cell.execute(cm.getValue())`.
3. Disable Run while busy and show the execution count or ✓/✗.

**SPA navigation:** the site is Remix, so pages change without a reload.
- Observe the `article` element with a debounced `MutationObserver`, and also watch `location.pathname`.
- On path change: dispose the current notebook and session, then re-scan.
- Wait for hydration before the first scan (`requestIdleCallback`, or poll until `.myst-jp-nb-block` exists).

**Hide MyST's power button:** CSS rule `.myst-jp-nb-toolbar { display: none !important; }`. Keep `project.jupyter.lite: true` in `myst.yml`, because it may be what makes MyST emit the thebe assets. Verify this in Task 5.

**Dark mode:** watch `html.dark` and switch the CodeMirror theme class.

### Task 3: Overlay CSS, `_static/editor/nma-editor.css`

- Style editors to match `.myst-code` (border-left accent, font, padding).
- Style the toolbars, status pill and busy spinner.
- Add `.nma-hidden { display: none }` and the power-toolbar hide rule.
- Add a dark-mode palette under `html.dark`.

### Task 4: Injection script, `scripts/inject_editor.py`

**Usage:** `python scripts/inject_editor.py [--build-dir _build/html] [--base-url ""]`

1. Copy `_static/editor/` to `<build>/_static/editor/`.
2. For every `index.html` under the build dir, add these before `</head>`:
   ```html
   <link rel="stylesheet" href="{base}/_static/editor/vendor/codemirror.min.css">
   <link rel="stylesheet" href="{base}/_static/editor/nma-editor.css">
   <script src="{base}/_static/editor/vendor/codemirror.min.js" defer></script>
   <script src="{base}/_static/editor/vendor/python.min.js" defer></script>
   <script src="{base}/_static/editor/nma-editor.js" defer></script>
   ```
   - Inject on all pages, not only executable ones, because SPA navigation can land on a tutorial from any page. The JS does nothing on pages without cells.
3. Make it idempotent: skip files that already contain `nma-editor.js`. Print the number of files patched. Exit non-zero if 0 files were patched or the build dir is missing.

**Tests, `tests/test_inject_editor.py` (pytest, written first):**
- injects into a fixture HTML file
- is idempotent when run twice
- copies the assets
- fails on a missing build dir
- respects the base URL

Add `pytest` as a dev dependency, e.g. in `requirements.txt` or through `uv run --with pytest`.

### Task 5: Wire into CI and local preview

**Files:** `.github/workflows/publish-book.yml`, `AGENTS.md`, `README.md`.

1. In CI, add a step after "Build MyST book": `run: uv run python scripts/inject_editor.py`.
2. Validate the workflow YAML: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/publish-book.yml'))"`.
3. Document local preview. Note that `myst start` will **not** show the editors:
   ```bash
   uv run myst build --html && uv run python scripts/inject_editor.py && python3 -m http.server -d _build/html 8000
   ```
4. In `AGENTS.md`, add an "Editable cells overlay" section covering:
   - the architecture
   - the mystmd pin and why it exists
   - the selectors the overlay relies on
   - "remove once mystmd#443 ships"
5. Confirm `_build/html/thebe-core.min.js` and `thebe-lite.min.js` exist after the build.

### Task 6: Browser verification (local, then deployed)

Run against the local build first, then against `https://template.neuromatch.io`.

1. **W1D1_Tutorial1:**
   - Every visible code cell shows an editor.
   - Edit `message = "..."` and run it; the edited output appears.
   - Shift-Enter runs the cell.
2. **W2D1_Tutorial1:**
   - Edit an exercise cell (`raise NotImplementedError`), fill it in, and run it; the plot appears.
   - `@widgets.interact` sliders work.
   - Video tabs render.
   - The vibecheck feedback widget renders.
   - A `hide-input` solution cell stays collapsed and is editable when opened.
3. **W1D2_Tutorial2:** the remove-cell setup runs automatically, and the Altair chart renders.
4. **State:** a variable defined in cell A is visible in cell B. Restart clears it.
5. **Navigation:** moving to another tutorial through the sidebar (client-side) re-mounts editors and gives a fresh kernel session.
6. **No conflicts:**
   - The power button is hidden.
   - There are no console errors and no 404s in the Network tab.
   - Only one Pyodide runtime loads.
7. **Dark mode** toggle looks right.

### Task 7: Commit

Make separate commits per task, for example:
- `build: pin mystmd 1.11.0`
- `feat: vendor CodeMirror 5`
- `feat: editable code cell overlay`
- `feat: post-build editor injection`
- `ci: inject editor overlay`
- `docs: editable cells overlay`

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| The thebe-core API differs from what we assumed | Task 0 spike happens before any other work, and the exit criteria gate the rest |
| React re-renders remove our nodes | Insert siblings and hide React nodes instead of replacing them; the MutationObserver re-mounts |
| A MyST upgrade changes classes or thebe | mystmd pinned; selectors documented in AGENTS.md |
| thebe assets not emitted | Keep `jupyter.lite: true`; Task 5 checks for the files |
| Widgets need `attachToDOM` on a stable node | Fall back to our own `.nma-output` div |

## Out of scope

- `myst start` live preview support
- Persisting edits across reloads (could use localStorage later)
- Upstream PR to mystmd#443
