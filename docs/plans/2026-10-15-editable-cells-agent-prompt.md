# Agent prompt: implement editable code cells

Copy everything below the line into a fresh agent session started in the
repository root (`course-template/`).

---

You are implementing **editable, runnable code cells** for this Neuromatch
MyST course template. The design and the plan are finished and approved. Your
job is to execute the plan task by task, with tests first, and to stop and ask
when reality contradicts the plan.

## Read first, in this order

1. `AGENTS.md`: project conventions, content rules, CI, and the sandbox notes
   (network approvals, `bash -l -c`, git workspace mode).
2. `docs/plans/2026-10-15-editable-cells-design.md`: the approved design. Its
   code sketches are the reference implementation. Its **appendix
   (`--execute`, pre-rendered outputs) is out of scope.**
3. `docs/plans/2026-10-15-editable-cells.md`: the implementation plan (8
   tasks, checkbox steps, exact names, copy, versions and tests).
4. For patterns to copy: `plugins/scrolly/scrolly.mjs` (document-stage
   transform emitting `anywidget` nodes), `plugins/scrolly/engine.mjs`
   (copying a stylesheet from a shadow root into `<head>`),
   `plugins/scrolly/runnable.mjs` (an existing runnable panel),
   `tests/js/scrolly.test.mjs` (AST test helpers), and the "run-all fallback"
   section of `tests/test_nma_solutions.py` (IPython shell tests).

## How to work

- Use the **superpowers:executing-plans** skill (or
  **superpowers:subagent-driven-development** if you have a subagent tool).
  Work through the tasks in order. Tick each `- [ ]` step in the plan file as
  you finish it, and commit the plan file along with the task's code.
- **TDD as written:** write the failing test, run it and see it fail for the
  expected reason, implement, then see it pass. One commit per task, using the
  plan's commit message.
- Before starting, check the workspace mode (`[ -d /run/sandbox/source ] &&
  echo clone || echo direct`) and create a branch:
  `git checkout -b feat/editable-cells`. Don't push or open a PR until the user
  asks.
- Follow the plan's **Global Constraints** exactly: pinned versions, the
  `runtime` values, the `nma-no-fallback` marker, all UI copy, CSS token names,
  and no root-absolute asset URLs in browser code.
- **Don't change** scrolly pages or their runtime, generated notebooks, or
  anything in the design's appendix. Don't add pre-rendered outputs, edit
  persistence or an `--execute` step.
- **Never commit `--prepare-site` output.** It edits `tutorials/*.md` in place.
  After using it for a local build, run `git checkout -- tutorials/`. CI
  rejects committed badges and fallback cells.
- If a step can't be done as written (for example, a thebe 0.5.0 method has
  a different name than the design assumes), pick the smallest change that
  keeps the plan's interfaces and tests intact. Add a short dated note under
  "Spike evidence" in the design doc. Stop and ask the user if it would change
  behaviour, copy, files or interfaces another task depends on.

## Environment notes (from the design session's sandbox)

- Node 22 is at `/usr/bin/node`. Python tooling goes through `uv run …`. If a
  tool isn't found, retry with `bash -l -c "…"`.
- `myst build` downloads the book theme from `api.mystmd.org`, which the
  sandbox firewall has blocked (403). The theme is cached in
  `_build/templates/`, so **don't delete `_build/` wholesale** (remove
  `_build/html` or `_build/site` if you need a clean build). If the cache is
  missing, ask the user to approve `api.mystmd.org` (see "Network access" in
  AGENTS.md).
- Reachable: `registry.npmjs.org`, `pypi.org`, Playwright's browser download,
  and `cdn.jsdelivr.net` (approved during design; thebe-lite loads Pyodide
  0.27 from it).
- Possibly blocked: `cdnjs.cloudflare.com`. thebe's widget manager loads
  `require.js` from it, and MathJax and font-awesome come from it too. If it's
  blocked, either ask the user to approve it, or for the local e2e run:
  `npm pack requirejs@2.3.6` into `/tmp`, extract it, and set
  `NMA_E2E_REQUIREJS=/tmp/package/require.js`. The plan's e2e `conftest.py`
  then blocks service workers and serves `require.js` from that file.
  Playwright can't intercept requests that go through JupyterLite's service
  worker. Missing MathJax/font-awesome only affects math in outputs and icons.
- The sandbox proxy re-signs TLS, so Playwright contexts need
  `ignore_https_errors=True`.
- Playwright setup that worked: `uv pip install playwright` then
  `uv run python -m playwright install chromium` (add `--with-deps` if system
  libraries are missing).
- `myst` exits 0 even with `⛔` errors, so read its output.
  `tutorials/W1D1_GettingStarted/W1D1_Tutorial3.md` has a known pre-existing
  `⛔ Unsupported image extension ".txt"` warning. Ignore it.
- If `/tmp/spike/` exists, it holds the throwaway spike from the design
  session. `cm/panel-src.mjs` is a working CodeMirror 6 + thebe panel, and
  `drive.py`, `widgets.py`, `nav.py`, `real.py` are Playwright harnesses. Use
  them for reference only. Don't copy the spike's shortcuts (`basicSetup`,
  per-cell notebooks, no hydration handling).

## Facts the spike verified (mystmd 1.11.0)

- On executable pages MyST loads `thebe-core.min.js` and `thebe-lite.min.js`,
  and `window.thebeCore.api` exposes `makeEvents`, `makeConfiguration`,
  `makeServer`, `makeRenderMimeRegistry` and `setupNotebookFromBlocks`. The
  server has `connectToJupyterLiteServer`, `startNewSession`,
  `shutdownAllSessions` and `dispose`. Cells have `execute(source?)` (an
  override works), `attachToDOM(el, skipIfAttached?)` and `executionCount`.
- MyST renders each `anywidget` node inside a shadow root on a host
  `div.myst-anywidget.<class>`, and loads the ESM with a dynamic `import()`
  of `<base>/build/<name>-<hash>.mjs`, so `import.meta.url` is the bundle
  URL.
- Output placed in light DOM and slotted into the shadow root gets the page's
  thebe/ipywidgets CSS. Output placed inside the shadow root would not.
- `@widgets.interact`, matplotlib with `%config`, `display(HTML)`, pandas,
  tracebacks and top-level `await micropip.install(...)` all work. First run is
  6–8 s.
- Panels can mount twice during hydration. CodeMirror's default keymap swallows
  Shift-Enter unless the run binding uses `Prec.highest`.
- Power button selector: `.myst-jp-nb-toolbar-power`. Theme classes:
  `html.light` / `html.dark`.

## Done means

Run all of these yourself, fresh, and paste the evidence into your final
message. Use the superpowers:verification-before-completion skill.

1. `uv run pytest -q`: all pass (e2e skipped without `NMA_E2E_URL`).
2. `node --test tests/js/*.test.mjs`: all pass.
3. `cd plugins/cells && npm run build && git diff --exit-code dist/`: clean.
4. `uv run python scripts/convert_to_notebooks.py --dry-run`: no validation
   errors.
5. A local site build with `--prepare-site` (then `git checkout --
   tutorials/`), served, and `NMA_E2E_URL=… uv run pytest -q tests/e2e`:
   **9 passed**.
6. `git status` is clean, with one commit per task on `feat/editable-cells`.

Final message:

- what was built, per task
- the verification output
- every deviation from the plan, and why
- anything you couldn't verify (for example, if cdnjs stayed blocked and you
  used the `require.js` workaround)
- open questions for the user
