# Course Kit (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the MyST plugins, notebook scripts, tests and CI out of the template into a self-contained, extractable `course-kit/` folder (future repo `neuromatch/course-kit`), and switch the template to use it, with identical output.

**Architecture:** `course-kit/python` is a pip-installable package (`nma_kit`, CLI `nma-kit`) built from today's `scripts/`. `course-kit/js` keeps one source folder per feature plugin (media, solutions, feedback, scrolly, cells, plus `shared/`) and bundles them into one `dist/nma.mjs` plus `dist/assets/` (browser widgets and CSS), with the asset base baked at build time (CDN URL for releases, project-relative path for dev). `course-kit/.github/workflows/` holds reusable `workflow_call` workflows that courses call, plus the kit's own CI and release workflows. The template keeps only content and a phase-1 workflow that installs the in-repo kit.

**Tech Stack:** Python ≥3.10 (hatchling, pyyaml, jupytext, nbclient, mystmd 1.11.0), Node 22 (esbuild, `yaml`, CodeMirror 6), GitHub Actions, release-please, pytest, `node --test`, Playwright.

**Spec:** `docs/plans/2026-10-16-course-kit-extraction-design.md`

## Global Constraints

- One version for everything; initial version `0.1.0` (stay on 0.x until the kit is stable) in `course-kit/js/package.json`, `course-kit/python/pyproject.toml` and `KIT_VERSION` in the reusable workflows.
- Names: npm `@neuromatch/course-kit`, PyPI `neuromatch-course-kit`, import package `nma_kit`, console script `nma-kit`, repo `neuromatch/course-kit`.
- The kit pins `mystmd==1.11.0` (cells rely on its bundled thebe 0.5.0 API).
- Release asset base: `https://cdn.jsdelivr.net/npm/@neuromatch/course-kit@<exact version>/dist/assets/`. Never an alias (`@0.1`, `@latest`) at build time.
- Courses never need Node/npm for their own content (phase 1 template is the one exception: it builds the in-repo dev bundle).
- Browser code never uses root-absolute URLs; derive from `import.meta.url` (unchanged rule).
- Output parity: generated notebooks and rendered page content must match the pre-move build (Task 9).
- The template's own build is expected to be broken between Task 2 and Task 9 (files are moving); keep the work on a branch and don't merge to `main` mid-way.
- New `nma:` settings and defaults: `nma.paths.tutorials` = `tutorials`, `nma.notebooks.branch` = `notebooks-branch`.
- `nma:` values must stay plain strings (CI keeps rejecting non-string values), now parsed with a real YAML parser on both sides.
- `course-kit/` must not import or read anything outside itself (except the course's `myst.yml`/content in the working directory at run time).
- Baseline before starting: `uv run pytest -q tests --ignore=tests/e2e` → 175 passed; `node --test tests/js/*.test.mjs` → 78 passed. Test counts may only go up.

## Review Focus

1. A course `myst.yml` with no `nma:` block, or one without the new keys → defaults apply, no error (Task 3).
2. A fresh fork with no `notebooks-branch` → `publish-notebooks` creates an orphan branch; a second run with no changes makes no commit (Task 4).
3. `extend:` written as a scalar or as a list, quoted or not, or with no kit URL at all → `pin_kit_url` rewrites only the kit URL, otherwise returns the text unchanged (Task 4).
4. A course with a custom tutorials dir (e.g. `content`) → Python badge/solution paths and the JS plugin's `pageLocation`/`notebookUrls` agree (shared fixture, Tasks 3 and 6).
5. Running `nma-kit` outside a course (no `myst.yml`) → one-line error naming the missing file, exit code 2, no traceback (Task 4).

---

### Task 1: Spike the MyST loading risks (throwaway)

Proves the spec's "Spike first" items before anything is moved. Work in `/tmp/kit-spike`, never in the repo. Only the findings note is committed.

**Files:**
- Modify: `docs/plans/2026-10-16-course-kit-extraction-design.md` (append a "Spike results" section)

- [ ] **Step 1: Build a tiny remote setup.** In `/tmp/kit-spike/remote/` put: `nma.yml` (extends with `project.plugins: [http://localhost:8790/nma.mjs]`, `jupyter.lite: true`), a one-file esbuild bundle of today's `plugins/nma.mjs` + `scrolly/scrolly.mjs` + `cells/cells.mjs` (with the `/plugins/...` asset constants replaced by `http://localhost:8790/assets/...`), and `assets/` containing `plugins/cells/dist/*.mjs`, `plugins/cells/*.css`, `plugins/scrolly/*.{mjs,css}`, `plugins/nma-feedback.mjs`. Serve it with `python3 -m http.server 8790`.
- [ ] **Step 2: Build a copy of the template that uses it.** Copy `tutorials/`, `_static/`, `myst.yml` to `/tmp/kit-spike/course/`; remove `project.plugins`; add `extend: http://localhost:8790/nma.yml`. Run `uv run --project /home/yuda/code/neuromatch/course-template myst build --html` there.
- [ ] **Step 3: Check items 1–4 and the dev path.** Record pass/fail for each:
  1. Build log shows the plugin loaded (`{nma-video}` renders as tabs on W1D2 Tutorial 4; no "unknown directive").
  2. `_build/html/build/` contains hashed copies of the remote `esm` **and** `css` assets.
  3. Serve `_build/html` and open W2D1 Tutorial 1 with the e2e test (`NMA_E2E_URL=… uv run pytest -q tests/e2e -k one_panel`) → thebe loads (panels run).
  4. Scrolly page (W2D1 Tutorial 2) layout CSS applies (`.scrolly-col` present, stage pinned).
  5. Dev path: with plugins listed as a local file outside the project root, an `esm` value like `/../kit/assets/x.mjs` (project-root-relative with `..`) resolves (MyST joins it onto the source path).
- [ ] **Step 4: Record results.** Append "Spike results" to the design doc: one line per item, plus the fallback taken for any failure (item 1 fails → list the plugin URL directly in the course `myst.yml` and have `pin_kit_url` rewrite that; item 3 fails → `thebeScriptUrls` resolves from `document.baseURI`/the page's `<script src*="thebe-core">` instead of `import.meta.url`; item 5 fails → `example-course` symlinks `_kit -> ../js/dist`). Item 5 of the spec (CNAME) is noted as "user verifies in repo Settings → Pages".
- [ ] **Step 5: Commit** `git add docs/plans/2026-10-16-course-kit-extraction-design.md && git commit -m "docs: course kit spike results"`. Later tasks use the recorded fallbacks where an item failed.

---

### Task 2: Python package `nma_kit` from `scripts/`

**Files:**
- Create: `course-kit/python/pyproject.toml`, `course-kit/python/src/nma_kit/__init__.py`
- Move (`git mv`): `scripts/convert_to_notebooks.py` → `course-kit/python/src/nma_kit/convert.py`; `scripts/nma_{media,solutions,feedback,scrolly,cells}.py` → `course-kit/python/src/nma_kit/{media,solutions,feedback,scrolly,cells}.py`
- Move: `tests/test_*.py` → `course-kit/tests/python/test_{convert,media,solutions,feedback,scrolly,cells}.py`; `tests/fixtures/` → `course-kit/fixtures/`
- Create: `course-kit/example-course/myst.yml` (minimal: title, `project.github: https://github.com/neuromatch/course-kit`, the same `nma:` block as today's template)
- Delete: `tests/conftest.py` (the `sys.path` hack)

**Interfaces:**
- Produces: `nma_kit.__version__ = "0.1.0"`; modules `nma_kit.convert|media|solutions|feedback|scrolly|cells` with today's public functions unchanged in name and signature; `nma_kit.FIXTURES` is not a thing — tests locate fixtures as `Path(__file__).parents[2] / "fixtures"`.

- [ ] **Step 1: Move files with `git mv`** (keeps history for the later subtree split) and replace intra-package imports (`import nma_cells` → `from nma_kit import cells as nma_cells`, etc.; keep local aliases so function bodies don't change).
- [ ] **Step 2: Write `pyproject.toml`.** hatchling, `name = "neuromatch-course-kit"`, `version = "0.1.0"`, `requires-python = ">=3.10"`, deps `mystmd==1.11.0, jupytext>=1.16, nbclient, nbformat, ipykernel, pyyaml`, optional `test = [pytest, playwright]`, `[project.scripts] nma-kit = "nma_kit.cli:main"` (cli lands in Task 4; add a stub `main()` that prints usage so the entry point resolves).
- [ ] **Step 3: Point tests at the kit.** Update imports in the moved tests, fixture paths to `course-kit/fixtures/...`, and `test_real_myst_yml_has_feedback_config` to read `course-kit/example-course/myst.yml`. Error strings that name `plugins/nma.mjs` (e.g. `FORMAT_ERROR`) now say "the course kit's MyST plugin"; update the assertions that match them.
- [ ] **Step 4: Run** `cd course-kit/python && uv venv && uv pip install -e '.[test]' && uv run pytest -q ../tests/python` → 175 passed.
- [ ] **Step 5: Commit** `git commit -m "refactor: move notebook scripts into course-kit python package"`.

---

### Task 3: Settings module and real YAML (Python)

**Files:**
- Create: `course-kit/python/src/nma_kit/config.py`, `course-kit/tests/python/test_config.py`, `course-kit/fixtures/config/settings.json`
- Modify: `convert.py`, `solutions.py`, `scrolly.py`, `feedback.py` (drop `TUTORIALS_DIR`/`NOTEBOOKS_BRANCH` constants and the line reader)

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Settings: github_repo: str | None; tutorials_dir: str; notebooks_branch: str; nma: dict`
  - `load_settings(myst_text: str) -> Settings` (pure, from text)
  - `read_settings(path: Path = Path("myst.yml")) -> Settings` (raises `MissingConfig(path)` if absent)
  - `read_nma_block(text: str) -> dict` now returns `yaml.safe_load(text)["nma"]` (or `{}`); `config_errors` rejects any non-dict section or non-`str` leaf with the existing `FORMAT_ERROR` wording.
  - `solution_url(repo, rel_dir, filename, branch)` and `make_badge_html(notebook_rel_path, github_repo, branch)` gain a `branch` parameter; `render_path(rel_dir, stem)` unchanged; `render_all(root)` / `process_tutorials(...)` take `settings: Settings`.
- `settings.json` is shared with JS (Task 6): a list of `{myst, page, expect: {relDir, stem, notebook, colab, kaggle, solution1}}` cases, including one with no `nma:` block and one with `nma.paths.tutorials: content` and `nma.notebooks.branch: nb`.

- [ ] **Step 1: Write failing tests** in `test_config.py`:
  - `test_defaults_without_nma_block`: `load_settings("project:\n  github: https://github.com/o/r\n")` → `tutorials_dir == "tutorials"`, `notebooks_branch == "notebooks-branch"`, `github_repo == "o/r"`.
  - `test_custom_paths`: `nma:\n  paths:\n    tutorials: content\n  notebooks:\n    branch: nb\n` → `"content"`, `"nb"`.
  - `test_shared_fixture_cases`: for each case in `fixtures/config/settings.json`, the Python badge/solution URLs equal `expect`.
  - `test_number_value_rejected`: `config_errors("nma:\n  feedback:\n    user_key: 123\n")` == `[FORMAT_ERROR]`.
  - existing `nma_config/*` fixture tests still pass unchanged.
- [ ] **Step 2: Run** `uv run pytest -q ../tests/python/test_config.py` → FAIL (`ModuleNotFoundError: nma_kit.config`).
- [ ] **Step 3: Implement** `config.py` and thread `Settings` through `convert.py`, `solutions.py`, `scrolly.py` (callers pass `settings.tutorials_dir`/`settings.notebooks_branch`). `load_github_repo` becomes a thin wrapper over `load_settings`.
- [ ] **Step 4: Run** the whole Python suite → all pass (≥ 175 + new).
- [ ] **Step 5: Commit** `git commit -m "feat(kit): configurable tutorials dir and notebooks branch"`.

---

### Task 4: `nma-kit` CLI

**Files:**
- Create: `course-kit/python/src/nma_kit/cli.py`, `course-kit/python/src/nma_kit/publish.py`, `course-kit/python/src/nma_kit/pin.py`, `course-kit/tests/python/test_cli.py`, `course-kit/tests/python/test_publish.py`, `course-kit/tests/python/test_pin.py`
- Modify: `convert.py`, `scrolly.py` (their `main()`s become thin and are no longer entry points)

**Interfaces:**
- Consumes: `read_settings`, `MissingConfig` (Task 3); `convert.validate_content`, `convert.process_tutorials`, `scrolly.render_all`.
- Produces:
  - `cli.main(argv: list[str] | None = None) -> int` with subcommands `check`, `notebooks [--dry-run]`, `render-scrolly`, `prepare-site [--dry-run] [--kit-version X]`, `publish-notebooks [--remote origin] [--message M]`.
  - `pin.pin_kit_url(myst_text: str, version: str) -> str`: replaces the version segment of any `https://cdn.jsdelivr.net/npm/@neuromatch/course-kit@<v>/` URL (in `extend:` scalar or list form, quoted or not) with `version`; returns input unchanged if none present.
  - `publish.publish_notebooks(src: Path, branch: str, remote: str, message: str) -> bool` (True if a commit was pushed).
  - `--kit-version` defaults to `nma_kit.__version__`.

- [ ] **Step 1: Write failing tests.**
  - `test_pin.py`: scalar `extend: https://cdn.jsdelivr.net/npm/@neuromatch/course-kit@0.1/dist/nma.yml` → `@0.1.3`; list form with a second unrelated URL untouched; quoted form; no kit URL → identical string.
  - `test_cli.py` (use `monkeypatch.chdir(tmp_path)`): no `myst.yml` → `main(["check"]) == 2` and stderr is one line containing `myst.yml`; a course with an exercise missing its solution → `main(["check"]) == 1`; `main(["prepare-site", "--kit-version", "9.9.9"])` rewrites the kit URL in `myst.yml` and adds badges (existing `--prepare-site` assertions reused); `main(["notebooks", "--dry-run"]) == 0` writes nothing.
  - `test_publish.py` (real git in `tmp_path`, a bare repo as `origin`): no remote branch → orphan branch created containing only `notebooks/`, returns True; rerun unchanged → returns False and no new commit; changed notebook → True, one new commit.
- [ ] **Step 2: Run** them → FAIL (missing modules).
- [ ] **Step 3: Implement.** `publish_notebooks` mirrors today's `generate-notebooks.yml` shell (worktree, `rsync --delete` equivalent via `shutil`, commit as `github-actions[bot]`, push); when `git ls-remote --heads <remote> <branch>` is empty, `git worktree add --orphan` (Git ≥2.42; fall back to `git checkout --orphan` in a temp worktree). Exit codes: 0 ok, 1 content/validation errors, 2 usage/missing config.
- [ ] **Step 4: Run** the full Python suite → all pass.
- [ ] **Step 5: Commit** `git commit -m "feat(kit): nma-kit CLI with pinning and notebooks publishing"`.

---

### Task 5: JS plugins split by feature

Organisation only; behaviour unchanged. Each feature is its own plugin
folder depending only on `shared/`.

**Files:**
- Move (`git mv`) and split:
  - `plugins/nma.mjs` → `course-kit/js/src/media/plugin.mjs` (`{nma-video}`, `{nma-slides}`, `VIDEO_SOURCES`), `course-kit/js/src/solutions/plugin.mjs` (`{nma-solution}`, `{nma-explanation}`, link transform), `course-kit/js/src/feedback/plugin.mjs` (`{nma-feedback}`, its transform, `defaultPrefix`, `pagePrefix`), `course-kit/js/src/shared/config.mjs` (`readNmaConfig`), `course-kit/js/src/shared/paths.mjs` (`githubRepo`, `pageLocation`, `notebookUrls`)
  - `plugins/nma-feedback.mjs` → `course-kit/js/src/feedback/assets/widget.mjs`
  - `plugins/scrolly/scrolly.mjs` → `course-kit/js/src/scrolly/plugin.mjs`; `plugins/scrolly/{engine,runnable}.mjs`, `*.css` → `course-kit/js/src/scrolly/assets/`; `exercisePairs` moves to `course-kit/js/src/shared/exercises.mjs` (cells and scrolly both use it); `isScrolly` to `shared/frontmatter.mjs`
  - `plugins/cells/cells.mjs` → `course-kit/js/src/cells/plugin.mjs`; `plugins/cells/src/*` → `course-kit/js/src/cells/src/`; `plugins/cells/*.css` → `course-kit/js/src/cells/assets/`
  - `plugins/cells/package*.json` → `course-kit/js/package*.json`
  - `tests/js/{nma,scrolly,cells}.test.mjs` → `course-kit/tests/js/{media,solutions,feedback,scrolly,cells,shared}.test.mjs` (tests split along the same lines)
- Create: `course-kit/js/src/index.mjs`, `course-kit/tests/js/structure.test.mjs`

**Interfaces:**
- Produces:
  - Each `src/<feature>/plugin.mjs` default-exports `{ name: string, directives?: [], transforms?: [] }`.
  - `src/index.mjs` default-exports `{ name: 'Neuromatch course kit', directives, transforms }`, merging plugins in the order `media, solutions, feedback, scrolly, cells` (keeps today's transform order: the three former `nma.mjs` transforms in their current order, then scrolly, then cells).
  - `src/shared/*` exports keep today's names and signatures (`readNmaConfig`, `githubRepo`, `pageLocation`, `notebookUrls`, `isScrolly`, `exercisePairs`).
  - Asset constants stay `'/plugins/...'`-style for now, pointing at the new paths (`/course-kit/js/src/<feature>/assets/...`). Task 6 replaces them.
  - `course-kit/js/package.json`: `"name": "@neuromatch/course-kit"`, `"version": "0.1.0"`, `"type": "module"`, script `test` (`node --test ../tests/js/*.test.mjs`).

- [ ] **Step 1: Write the failing structure test** `structure.test.mjs`: for every `src/<feature>/` folder (excluding `shared`), no file imports from another feature folder (scan `import … from '../<other>/'`); `index.mjs`'s directive names are exactly `nma-video, nma-slides, nma-solution, nma-explanation, nma-feedback, step, stage` (plus any others existing today; take the list from the current plugins before moving); transform names in index order match today's `myst.yml` plugin order.
- [ ] **Step 2: Run** `cd course-kit/js && npm test` → FAIL (no `src/`).
- [ ] **Step 3: Move and split** with `git mv` first (one file per old file), then extract the pieces into the new files. Update test imports (`../../plugins/...` → `../../js/src/...`). Tests that read the real `myst.yml` read `course-kit/example-course/myst.yml`; `notebookUrls(join(process.cwd(), 'tutorials/…'))` runs after `process.chdir` to `example-course`.
- [ ] **Step 4: Run** `npm ci && npm test` → all pass (≥ 78 + structure tests).
- [ ] **Step 5: Commit** `git commit -m "refactor: course-kit js plugins organised by feature"`.

---

### Task 6: One bundle, versioned assets, real YAML

**Files:**
- Create: `course-kit/js/src/shared/assets.mjs`, `course-kit/js/build.mjs`, `course-kit/js/nma.yml.tmpl`, `course-kit/js/.gitignore` (`dist/`, `node_modules/`), `course-kit/tests/js/{config,bundle}.test.mjs`
- Modify: every plugin's asset constants; `shared/config.mjs`, `shared/paths.mjs`; `course-kit/js/package.json`

**Interfaces:**
- Consumes: `src/index.mjs` and plugin layout (Task 5); `course-kit/fixtures/config/settings.json` (Task 3).
- Produces:
  - `package.json`: `"files": ["dist"]`, scripts `build` (release), `build:dev`; deps add `yaml`.
  - `dist/nma.mjs`: the bundle of `src/index.mjs`.
  - `dist/assets/<feature>/…`: `feedback/widget.mjs`, `scrolly/{engine,runnable}.mjs`, `scrolly/*.css`, `cells/{panel,runtime-widget}.mjs`, `cells/*.css`.
  - `dist/nma.yml` from `nma.yml.tmpl` with the exact version (release build only); `dist/build-info.json` = `{mode: 'release'|'dev', version}`.
  - `shared/assets.mjs`: `export function assetUrl(rel: string): string` → `__NMA_ASSET_BASE__ + rel` when defined (release), else `'/' + relative(process.cwd(), <dir of import.meta.url>/assets/rel)` with forward slashes (dev). All asset constants become `assetUrl('<feature>/<file>')`.
  - `readNmaConfig(text)` keeps its name and return shape, implemented with `yaml.parse`; `githubRepo()`/`pageLocation()` read `nma.paths.tutorials`; the notebooks branch reads `nma.notebooks.branch`.

- [ ] **Step 1: Write failing tests.**
  - `config.test.mjs`: every case in `fixtures/config/settings.json` → `pageLocation`/`notebookUrls`/solution URL equal `expect` (chdir to a temp dir holding the case's `myst.yml`); quoted values stay strings (`readNmaConfig('nma:\n  a:\n    b: "1"\n').a.b === '1'`); the existing `nma_config/*` fixtures pass unchanged. Rejecting non-string values stays the Python `check`'s job.
  - `bundle.test.mjs` reads `dist/build-info.json` and runs the release assertions only in release mode: `import('../../js/dist/nma.mjs')` default export has the same directive names as `src/index.mjs`; the bundle text contains `cdn.jsdelivr.net/npm/@neuromatch/course-kit@0.1.0/dist/assets/` and no `/plugins/` or `/course-kit/`; `dist/nma.yml` lists `…@0.1.0/dist/nma.mjs` and `lite: true`; every path the bundle references under `dist/assets/` exists.
- [ ] **Step 2: Run** `npm test` → the new tests FAIL.
- [ ] **Step 3: Implement** `assets.mjs`, `build.mjs` (esbuild: entry `src/index.mjs` → `dist/nma.mjs`, `platform: 'node'`, `format: 'esm'`, `define: {__NMA_ASSET_BASE__: JSON.stringify(base) | 'undefined'}`; browser entries `src/cells/src/{panel,runtime-widget}.mjs` → `dist/assets/cells/` minified with the existing "GENERATED" banner; copy the other `src/<feature>/assets/*` to `dist/assets/<feature>/`; write `dist/nma.yml` and `build-info.json`). Release base reads the version from `package.json`.
- [ ] **Step 4: Run** `npm run build && npm test` → all pass; then `npm run build:dev && npm test` → all pass (release-only assertions skipped).
- [ ] **Step 5: Commit** `git commit -m "feat(kit): single bundled plugin with versioned assets"`.

---

### Task 7: `example-course` and the browser smoke test

**Files:**
- Create: `course-kit/example-course/` — `tutorials/W2D1_Examples/{W2D1_Tutorial1,W2D1_Tutorial2,W2D1_Tutorial3}.md`, `tutorials/W1D1_GettingStarted/W1D1_Tutorial1.md` (copies of the template pages the e2e test and scrolly render use), `tutorials/intro.md`, `requirements.txt` (numpy, matplotlib, ipywidgets, scipy), and complete `myst.yml` (toc for those pages, `jupyter.lite: true`, `plugins: [../js/dist/nma.mjs]`)
- Move: `tests/e2e/` → `course-kit/tests/e2e/` (`ROOT` → `course-kit/example-course`)
- Create: `course-kit/scripts/build-example.sh`

**Interfaces:**
- Consumes: `nma-kit` (Task 4), dev bundle (Task 6).
- Produces: `build-example.sh` = `npm run build:dev` in `js/`, then in `example-course/`: `nma-kit check && nma-kit render-scrolly && nma-kit prepare-site && myst build --html`, then `git checkout -- .` (so `prepare-site` edits are never committed). Used by kit CI and by humans.

- [ ] **Step 1: Copy pages, write `myst.yml`, move the e2e tests.** If spike item 5 failed, use the recorded fallback (symlink) for the plugin/asset path.
- [ ] **Step 2: Run** `bash course-kit/scripts/build-example.sh` → `_build/html` exists, no `⛔` in the log.
- [ ] **Step 3: Run** `(cd course-kit/example-course/_build/html && python3 -m http.server 8765 &) ; NMA_E2E_URL=http://localhost:8765 uv run --project course-kit/python pytest -q course-kit/tests/e2e` (set `NMA_E2E_REQUIREJS` if cdnjs is blocked) → all pass.
- [ ] **Step 4: Commit** `git commit -m "test(kit): example course and browser smoke test"`.

---

### Task 8: Workflows: reusable, kit CI, release

**Files:**
- Create in `course-kit/.github/workflows/`: `course-check.yml`, `course-publish.yml`, `course-wheels.yml`, `ci.yml`, `release.yml`
- Create: `course-kit/release-please-config.json`, `course-kit/.release-please-manifest.json` (`{".": "0.1.0"}`), `course-kit/templates/course.yml`
- Move: `.github/workflows/build-pyodide-wheels.yml` logic → `course-wheels.yml` (then delete the old file in Task 9)

**Interfaces:**
- Consumes: `nma-kit` subcommands (Task 4), `build-example.sh` (Task 7).
- Produces:
  - `course-check.yml` / `course-publish.yml`: `on: workflow_call`, inputs `python-version` (default `"3.12"`), `requirements` (default `requirements.txt`), `kit-version` (default empty = `env.KIT_VERSION`), `working-directory` (default `.`). `env.KIT_VERSION: 0.1.0` (release-please `x-release-please-version` marker). Install step: `uv venv && uv pip install -r $requirements "neuromatch-course-kit==$KIT_VERSION"` (`latest` → unpinned). `astral-sh/setup-uv` with `enable-cache: true`; `actions/setup-node` Node 22.
  - `course-publish.yml` job order: `nma-kit check` → `nma-kit notebooks` → `nma-kit publish-notebooks` (job-level `concurrency: notebooks-${{ github.repository }}`) → `nma-kit render-scrolly` → `nma-kit prepare-site` → `myst build --html` → `upload-pages-artifact` → `deploy-pages`. No CNAME step.
  - `course-wheels.yml`: input `packages`; builds wheels as today, commits them to `_wheels/` on the default branch.
  - `ci.yml`: pytest, `npm ci && npm run build && npm test`, `build-example.sh`, Playwright e2e; plus jobs calling `./.github/workflows/course-check.yml` with `working-directory: example-course` (and a `kit-source: local` path so it installs `./python` instead of PyPI; add that input to both reusable workflows, default `pypi`).
  - `release.yml`: `googleapis/release-please-action`; on release created: `npm publish --provenance --access public` (OIDC, `id-token: write`), `pypa/gh-action-pypi-publish` in environment `release`, then move the floating tags to the release commit: `v<major>.<minor>` and `v<major>` (during 0.x the template uses `v0.1`; from 1.0 courses use `v<major>`).
  - `release-please-config.json`: `release-type: simple`, `bump-minor-pre-major: true`, `bump-patch-for-minor-pre-major: true` (so breaking → 0.2.0, feat/fix → 0.1.x), `extra-files` = the two reusable workflows, `python/pyproject.toml`, `js/package.json`.
  - `templates/course.yml`: the caller from the spec, verbatim, at `@v0.1`.

- [ ] **Step 1: Write the workflows.**
- [ ] **Step 2: Lint** `uvx --from actionlint-py actionlint course-kit/.github/workflows/*.yml course-kit/templates/course.yml` → no errors (if the download is blocked, `python3 -c "import yaml,glob;[yaml.safe_load(open(f)) for f in glob.glob('course-kit/.github/workflows/*.yml')]"` and note that actionlint must run in the kit repo's CI).
- [ ] **Step 3: Check the release marker** `grep -n "x-release-please-version" course-kit/.github/workflows/course-*.yml` → one hit per reusable workflow; `release-please-config.json` lists them under `extra-files` together with `python/pyproject.toml` and `js/package.json`.
- [ ] **Step 4: Commit** `git commit -m "ci(kit): reusable course workflows, kit CI and release"`.

---

### Task 9: Switch the template to the in-repo kit, with a golden check

**Files:**
- Create: `course-kit/scripts/compare_builds.py`, `.github/workflows/course.yml` (phase-1 template workflow)
- Modify: `myst.yml` (`project.plugins: [course-kit/js/dist/nma.mjs]`), `requirements.txt` (content deps only: altair, vega_datasets, matplotlib, numpy, pandas, ipywidgets, scipy), `.gitignore`
- Delete: `plugins/`, `scripts/`, `tests/`, `.github/workflows/{generate-notebooks,publish-book,build-pyodide-wheels}.yml`, the CNAME copy step (the `CNAME` file stays until the user confirms the custom domain in Settings → Pages)

**Interfaces:**
- Consumes: everything above.
- Produces: `compare_builds.py <before_dir> <after_dir>` exits 0 iff (a) `notebooks/**` files are byte-identical, and (b) each `_build/site/content/*.json` matches after normalising `anywidget` `esm`/`css` values to their basename without hash. Prints the first differing file and JSON path otherwise.

- [ ] **Step 1: Build "before".** `git worktree add /tmp/before main` (on `main`): `uv run python scripts/convert_to_notebooks.py && uv run python scripts/nma_scrolly.py --render && uv run python scripts/convert_to_notebooks.py --prepare-site && uv run myst build --html`.
- [ ] **Step 2: Switch the template** (edits/deletions above). The phase-1 `.github/workflows/course.yml` has the same job order as `course-publish.yml` plus `on: pull_request` running the check steps, but installs with `uv pip install -r requirements.txt ./course-kit/python` and runs `npm ci && npm run build:dev` in `course-kit/js` first.
- [ ] **Step 3: Build "after"** in the repo: `npm run build:dev` in `course-kit/js`, then `nma-kit notebooks && nma-kit render-scrolly && nma-kit prepare-site && myst build --html`, then `git checkout -- tutorials myst.yml`.
- [ ] **Step 4: Run** `uv run --project course-kit/python python course-kit/scripts/compare_builds.py /tmp/before .` → exit 0. Any diff is a bug in Tasks 2–5 unless it's an asset filename (already normalised).
- [ ] **Step 5: Run** the e2e smoke test against the template's `_build/html` (as in Task 7 Step 3, with `NMA_E2E_URL` pointing at it) → pass.
- [ ] **Step 6: Commit** `git commit -m "refactor: template uses in-repo course kit"`.

---

### Task 10: Docs

**Files:**
- Create: `course-kit/README.md` (what it is, versioning table and "about latest" from the spec, local dev, registry setup steps from the spec), `course-kit/AGENTS.md` (the plugin/script internals, twin rules, bundles, CI sections moved from the template's AGENTS.md), `course-kit/CHANGELOG.md` (release-please seed), `course-kit/LICENSE` (copy of the template's BSD-3)
- Modify: `AGENTS.md` (keep authoring conventions; replace architecture/build/CI sections with a pointer to `course-kit/AGENTS.md` and the phase-1 commands), `README.md` ("After forking": Pages source = GitHub Actions; `notebooks-branch` is created automatically; set your custom domain in Settings → Pages), tutorials `W1D1_Tutorial4.md`, `W1D2_Tutorial4.md`, `W1D2_Tutorial6.md`, `W1D3_Tutorial1.md`, `W1D3_Tutorial2.md` (replace `scripts/…`/`plugins/…` paths with `nma-kit …` commands and "the course kit"; W1D3 T1 `literalinclude`s `.github/workflows/course.yml`)

- [ ] **Step 1: Write/modify the files.**
- [ ] **Step 2: Check** `grep -rn "scripts/\|plugins/" AGENTS.md README.md tutorials/` → no hits except deliberate historical mentions; `grep -rn "\.\./" course-kit --include=*.py --include=*.mjs --include=*.yml | grep -v node_modules | grep -v "example-course\|tests/"` → nothing reaching outside `course-kit/`.
- [ ] **Step 3: Run** `bash course-kit/scripts/build-example.sh` and the template build from Task 9 Step 3 → no `⛔`.
- [ ] **Step 4: Commit** `git commit -m "docs: course kit README/AGENTS, template docs point at the kit"`.

---

## After this plan (not tasks here)

Extraction (`git subtree split --prefix=course-kit -b course-kit-export`, push to `neuromatch/course-kit`), registry setup, first release `v0.1.0`, and phase 2 (template uses `extend:` + `templates/course.yml@v0.1`, `course-kit/` removed) follow the spec's "Delivery in two phases" and "Registry setup".
