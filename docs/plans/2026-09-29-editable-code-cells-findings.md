# Editable Code Cells: Investigation Findings

**Date:** 2026-09-29
**Status:** Findings complete, ready for design and implementation planning

## Problem Statement

Students need to edit exercise code cells (those with `raise NotImplementedError`) directly in the browser and re-run them. Currently, clicking the JupyterLite power button boots a kernel and allows running cells, but the code text remains static -- students cannot modify the code inline.

## Root Cause

**Editing code cells is an unimplemented feature in mystmd.** This is tracked as [jupyter-book/mystmd#443](https://github.com/jupyter-book/mystmd/issues/443) -- "[thebe] Enable editing code cells" -- open since June 2023, assigned to a maintainer, labeled `enhancement`. The issue explicitly states:

> "The implementation of Thebe used by mystmd allows code cells to be *run* with a back-end Binder or JupyterHub kernel. However, it does not allow code cells to be *edited* and re-run."

MyST's thebe integration only replaces the output area and attaches a kernel for execution. The code input stays as a static syntax-highlighted `<pre><code>` block. There is no CodeMirror editor.

## What We Tried (and What We Learned)

### Subpath deployment bugs (fixed, but irrelevant to editing)

We initially investigated and fixed two real bugs in thebe's GitHub Pages subpath handling:

1. **`thebe-core.min.js`** has `__webpack_require__.p="/"` hardcoded, causing chunk loading 404s on subpath deployments. We patched this in CI.
2. **`thebe-lite.min.js`** constructs the service worker URL at `https://neuromatch.github.io/service-worker.js` instead of `https://neuromatch.github.io/course-template/service-worker.js`, causing a 404.

We then switched to a custom domain (`template.neuromatch.io`) to eliminate all subpath issues. The kernel now boots successfully, cells can be *run*, but still cannot be *edited*. This confirmed the issue is not deployment-related -- it's a missing feature.

### Current state of the deployed site

- **Custom domain:** `template.neuromatch.io` (CNAME configured, deployed at root `/`)
- **Kernel boots:** Pyodide loads successfully (numpy, matplotlib, scipy, etc.)
- **Cells run:** Clicking run sends original source to kernel, output appears
- **Cells NOT editable:** Code stays as static `<pre><code>`, no CodeMirror editor

## Reference Implementation

The site at https://chandraveshchaudhari.github.io/jupyterbook2_with_lite_template/ has editable, runnable cells. **It does NOT use MyST's thebe integration.** Instead, it uses a fully custom solution:

**Repository:** https://github.com/chandraveshchaudhari/jupyterbook2_with_lite_template

### Architecture

1. **Custom MyST directive** (`pyodide-cell`) in `plugins/` -- renders `<div class="pyodide-cell-react">` containers with embedded source code
2. **Custom template** in `templates/` -- injects CodeMirror and Pyodide scripts into the page `<head>`
3. **Static assets** in `_static/`:
   - `codemirror/codemirror.js` + `codemirror.css` + `python.js` -- standalone CodeMirror editor
   - `pyodide-runner.js` -- connects CodeMirror editors to Pyodide kernel
   - `pyodide-transform.js` -- transforms directive divs into live editors on page load
   - `pyodide.css` -- styling for cells
4. **`patch_theme.py`** -- post-build script that patches the HTML theme

### How their cells work in the HTML

```html
<!-- In <head>: -->
<link rel="stylesheet" href="/_static/codemirror/codemirror.css"/>
<link rel="stylesheet" href="/_static/pyodide.css"/>
<script src="/_static/pyodide/pyodide.js" defer></script>
<script src="/_static/codemirror/codemirror.js" defer></script>
<script src="/_static/codemirror/python.js" defer></script>
<script src="/_static/pyodide-runner.js" defer></script>
<script src="/_static/pyodide-transform.js" defer></script>

<!-- Cell placeholder in body: -->
<div class="pyodide-cell-react not-prose col-body" id="pycell-hello"
     role="region" aria-label="Interactive Python cell"></div>
```

The JavaScript finds these divs, reads the source code from the page's JSON AST data, creates a CodeMirror editor with the source, and connects it to a shared Pyodide instance.

### Key differences from our setup

| Aspect | Their approach | Our current approach |
|--------|---------------|---------------------|
| Editor | CodeMirror (standalone) | None (static `<pre>`) |
| Kernel | Pyodide loaded directly | JupyterLite via thebe-lite |
| Cell directive | Custom `pyodide-cell` | Standard `{code-cell}` |
| Activation | Automatic on page load | Manual power button click |
| Template | Custom (injects scripts) | Default book-theme |

## Options for Implementation

### Option A: Adapt the reference implementation

Port the custom Pyodide+CodeMirror approach from the reference repo. This means:
- Adding a custom MyST plugin/directive or a post-build script
- Bundling CodeMirror as a static asset
- Writing JavaScript to transform existing `{code-cell}` blocks into editable CodeMirror editors connected to Pyodide
- Could work alongside or replace the existing thebe integration

**Pros:** Proven working approach, full control over behavior
**Cons:** Significant custom code to maintain, diverges from mystmd ecosystem

### Option B: Post-build JavaScript injection

Instead of a custom directive, inject a script via the template or `_static/` that:
- Detects all `{code-cell}` blocks on the page (they have `kind: "notebook-code"` in the AST)
- Replaces the static `<pre><code>` with a CodeMirror editor
- Connects to Pyodide directly (not through thebe)
- Adds run buttons

**Pros:** Works with existing `{code-cell}` syntax, no changes to tutorial `.md` files
**Cons:** Fragile if MyST's HTML structure changes, more complex DOM manipulation

### Option C: Wait for upstream mystmd#443

Wait for the mystmd team to implement editing in thebe.

**Pros:** No custom code
**Cons:** No timeline, could be months or years

## Relevant Files in Our Project

- `myst.yml` -- config with `project.jupyter.lite: true`
- `_static/custom.css` -- currently empty, can add cell styling
- `.github/workflows/publish-book.yml` -- CI build and deploy
- `tutorials/W2D1_Examples/W2D1_Tutorial1.md` -- real content with exercise cells
- Exercise cells have `raise NotImplementedError` and NO tags (correct per convention)

## Constraints

- Must work with the existing `{code-cell}` directive syntax in tutorial `.md` files (we have many tutorials already written)
- Must work in Pyodide/WebAssembly (no server-side kernel)
- Packages needed: numpy, matplotlib, scipy, ipywidgets (all available in Pyodide)
- Should support `hide-input` tag (solutions stay hidden, exercises stay visible and editable)
- Should share kernel state across cells on the same page
- CNAME is set to `template.neuromatch.io` (site deploys at root `/`)
